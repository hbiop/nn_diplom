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

            # Добавьте поле progress в модель, если ещё не сделали
            # progress = models.FloatField(default=0)

            # 1. Загрузка данных (10%)
            self.update_progress(10, "Загрузка данных")
            df = pd.read_csv(self.session.dataset.file.path)

            # 2. Загрузка модели и препроцессора (20%)
            self.update_progress(20, "Загрузка модели и препроцессора")
            training_session = self.session.model
            self.preprocessor = training_session.load_preprocessor()
            nn = training_session.load_neural_network()

            if not self.preprocessor or not nn:
                raise ValueError("Модель или препроцессор не найдены")

            # 3. Предобработка
            # данных (30%)
            self.update_progress(30, "Предобработка данных")
            X = self.preprocessor.preprocess_data_for_predict(df)

            # 4. Предсказание (40-80%)
            # Будем обновлять прогресс в процессе предсказания
            total_rows = len(X)
            predictions = []

            # Для батчей размером 1000
            batch_size = 1000
            num_batches = (total_rows + batch_size - 1) // batch_size

            for i in range(0, total_rows, batch_size):
                batch = X[i:i + batch_size]
                batch_predictions = nn.predict(batch).tolist()
                predictions.extend(batch_predictions)

                # Рассчитываем текущий прогресс
                processed = min(i + batch_size, total_rows)
                progress = 40 + 40 * (processed / total_rows)  # 40-80% диапазон

                self.update_progress(
                    progress,
                    f"Выполнение предсказаний: {processed}/{total_rows} строк"
                )

            # 5. Сохранение результатов (90%)
            self.update_progress(90, "Сохранение результатов")
            self.save_results(df, predictions)

            # Завершение (100%)
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

            # Также обновляем прогресс при ошибке
            self.update_progress(0, f"Ошибка: {str(e)}")

    def update_progress(self, progress, message):
        try:
            # Обновляем сессию в базе данных
            self.session.refresh_from_db()

            # Обрезаем прогресс до диапазона 0-100
            progress = max(0, min(100, progress))

            # Обновляем поля
            self.session.progress = progress
            self.session.logs = message

            # Сохраняем только если статус всё ещё 'running'
            if self.session.status == 'running':
                self.session.save()
        except Exception as e:
            print(f"Ошибка при обновлении прогресса: {e}")

    def predict_in_batches(self, model, X, batch_size=1000):
        """Разбивает предсказания на батчи для экономии памяти"""
        predictions = []
        for i in range(0, len(X), batch_size):
            batch = X[i:i + batch_size]
            predictions.extend(model.predict(batch).tolist())
        return predictions

    def save_results(self, original_df, predictions):
        """Многопоточное сохранение результатов"""
        # Разделяем данные на части для параллельной обработки
        num_threads = 4
        chunk_size = len(original_df) // num_threads
        chunks = [
            (original_df.iloc[i:i + chunk_size],
             predictions[i:i + chunk_size])
            for i in range(0, len(original_df), chunk_size)
        ]

        # Создаем и запускаем потоки
        threads = []
        for i, (df_chunk, pred_chunk) in enumerate(chunks):
            thread = threading.Thread(
                target=self._save_chunk,
                args=(self.session, df_chunk, pred_chunk, i)
            )
            threads.append(thread)
            thread.start()

        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()

        # Сохранение в файл (в главном потоке)
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
                # Получаем текущий прогноз
                current_pred = pred_chunk[i]

                # Для вычислений используем numpy array
                pred_array = np.array(current_pred)

                prediction_data = {
                    'raw': current_pred,  # Уже список, не нужно преобразовывать
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
    # Создаем и запускаем поток для предсказаний
    prediction_thread = PredictionThread(session)
    prediction_thread.start()

    # Можно вернуть ответ сразу, не дожидаясь завершения
    return JsonResponse({
        'status': 'started',
        'session_id': session_id,
        'message': 'Предсказание запущено в фоновом режиме'
    })