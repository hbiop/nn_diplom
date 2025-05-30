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
        self.session = session
        self.daemon = True  # Поток завершится при завершении главного процесса

    def run(self):
        try:
            self.session.refresh_from_db()
            self.session.status = 'running'
            self.session.save()

            # 1. Загрузка данных
            df = pd.read_csv(self.session.dataset.file.path)

            # 2. Загрузка модели и препроцессора
            training_session = self.session.model
            preprocessor = training_session.load_preprocessor()
            nn = training_session.load_neural_network()

            if not preprocessor or not nn:
                raise ValueError("Модель или препроцессор не найдены")

            # 3. Предобработка данных
            X = preprocessor.preprocess_data_for_predict(df)

            # 4. Предсказание (может быть разбито на части)
            predictions = self.predict_in_batches(nn, X, batch_size=1000)

            # 5. Сохранение результатов
            self.save_results(df, predictions)

            self.session.refresh_from_db()
            self.session.status = 'completed'
            self.session.predictions_count = len(predictions)
            self.session.save()

        except Exception as e:
            self.session.refresh_from_db()
            self.session.status = 'failed'
            self.session.logs = f"Ошибка: {str(e)}"
            self.session.save()

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
        """Сохранение части данных в отдельном потоке"""
        with transaction.atomic():
            results = []
            for i, (_, row) in enumerate(df_chunk.iterrows()):
                results.append(PredictionResult(
                    session=session,
                    input_data=row.to_dict(),
                    prediction=pred_chunk[i],
                    confidence=np.max(pred_chunk[i]) if isinstance(pred_chunk[i], (list, np.ndarray)) else None
                ))

            PredictionResult.objects.bulk_create(results)


def start_prediction(request, session_id):
    session = PredictSession.objects.get(id=session_id)

    # Создаем и запускаем поток для предсказаний
    prediction_thread = PredictionThread(session)
    prediction_thread.start()

    # Можно вернуть ответ сразу, не дожидаясь завершения
    return JsonResponse({
        'status': 'started',
        'session_id': session_id,
        'message': 'Предсказание запущено в фоновом режиме'
    })