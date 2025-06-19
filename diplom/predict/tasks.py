import threading
import pandas as pd
import numpy as np
from django.db import transaction
from io import StringIO
from django.core.files.base import ContentFile
import time

from django.http import JsonResponse
from predict.models import PredictionResult

from predict.models import PredictSession


class PredictionThread(threading.Thread):
    def __init__(self, session):
        threading.Thread.__init__(self)
        self.preprocessor = None
        self.session = session

    def run(self):
        try:
            self.session.refresh_from_db()
            self.session.status = 'running'
            self.session.save()

            self.update_progress(10, "Загрузка данных")
            df = pd.read_csv(self.session.dataset.file.path)

            if self.session.dataset.file_type == 'CSV':
                df = pd.read_csv(self.session.dataset.file.path)
            elif self.session.dataset.file_type == 'XLSX':
                df = pd.read_excel(self.session.dataset.file.path)

            self.update_progress(20, "Загрузка модели и препроцессора")
            training_session = self.session.model
            self.preprocessor = training_session.load_preprocessor()
            nn = training_session.load_neural_network()

            if not self.preprocessor or not nn:
                raise ValueError("Модель или препроцессор не найдены")


            self.update_progress(30, "Предобработка данных")
            X = self.preprocessor.preprocess_data_for_predict(df)


            total_rows = len(X)
            predictions = []


            batch_size = 1000
            num_batches = (total_rows + batch_size - 1) // batch_size

            for i in range(0, total_rows, batch_size):
                batch = X[i:i + batch_size]
                batch_predictions = nn.predict(batch).tolist()
                predictions.extend(batch_predictions)


                processed = min(i + batch_size, total_rows)
                progress = 40 + 40 * (processed / total_rows)

                self.update_progress(
                    progress,
                    f"Выполнение предсказаний: {processed}/{total_rows} строк"
                )

            self.update_progress(90, "Сохранение результатов")
            self.save_results(df, predictions)

            self.update_progress(100, "Предсказание успешно завершено")
            self.session.refresh_from_db()
            self.session.status = 'completed'
            self.session.predictions_count = len(predictions)
            self.session.save()

        except Exception as e:
            self.session.refresh_from_db()
            self.session.status = 'failed'
            self.session.logs = f"Ошибка: {str(e)}"
            self.session.save()


            self.update_progress(0, f"Ошибка: {str(e)}")

    def update_progress(self, progress, message):
        try:

            self.session.refresh_from_db()

            progress = max(0, min(100, progress))

            self.session.progress = progress
            self.session.logs = message

            if self.session.status == 'running':
                self.session.save()
        except Exception as e:
            print(f"Ошибка при обновлении прогресса: {e}")

    def predict_in_batches(self, model, X, batch_size=1000):
        predictions = []
        for i in range(0, len(X), batch_size):
            batch = X[i:i + batch_size]
            predictions.extend(model.predict(batch).tolist())
        return predictions

    def save_results(self, original_df, predictions):
        num_threads = 4
        chunk_size = len(original_df) // num_threads
        chunks = [
            (original_df.iloc[i:i + chunk_size],
             predictions[i:i + chunk_size])
            for i in range(0, len(original_df), chunk_size)
        ]

        threads = []
        for i, (df_chunk, pred_chunk) in enumerate(chunks):
            thread = threading.Thread(
                target=self._save_chunk,
                args=(self.session, df_chunk, pred_chunk, i)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        output_df = original_df.copy()
        output_df['prediction'] = predictions

        output = StringIO()
        output_df.to_csv(output, index=False)
        self.session.results_file.save(
            f'predictions_{self.session.id}.csv',
            ContentFile(output.getvalue().encode('utf-8'))
        )

    def _save_chunk(self, session, df_chunk, pred_chunk, chunk_id):
        with transaction.atomic():
            results = []
            for i, (_, row) in enumerate(df_chunk.iterrows()):

                current_pred = pred_chunk[i]

                pred_array = np.array(current_pred)

                prediction_data = {
                    'raw': current_pred,
                    'class': self.preprocessor.get_predicted_label(pred_array),
                    'confidence': float(np.max(pred_array))
                }

                results.append(PredictionResult(
                    session=session,
                    input_data=row.to_dict(),
                    prediction=prediction_data
                ))

            PredictionResult.objects.bulk_create(results)


def start_prediction(session_id):
    session = PredictSession.objects.get(id=session_id)
    print("start prediction here")

    prediction_thread = PredictionThread(session)
    prediction_thread.start()


    return JsonResponse({
        'status': 'started',
        'session_id': session_id,
        'message': 'Предсказание запущено в фоновом режиме'
    })