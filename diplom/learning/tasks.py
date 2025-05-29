import threading
import pickle
import numpy as np
import pandas as pd
from django.db import connection
from django.utils import timezone

from .data_preprocessor import DataPreprocessor
from .models import TrainingSession, TrainingEpoch
from .neural_network import NeuralNetwork


class TrainingThread(threading.Thread):
    def __init__(self, session_id):
        threading.Thread.__init__(self)
        self.session_id = session_id
        self.daemon = True  # Поток завершится при завершении основного процесса

    def run(self):
        # Закрываем соединение с БД основного потока
        connection.close()
        print("start")
        try:
            session = TrainingSession.objects.get(id=self.session_id)
            session.status = 'running'
            session.save()
            print("data loading")
            # Загрузка данных
            df = pd.read_csv(session.dataset.file.path)
            # Инициализация и обучение препроцессора

            preprocessor = DataPreprocessor()
            last_column_name = df.columns[-1]
            #last_column = df[last_column_name]
            X_train, X_test, y_train, y_test = preprocessor.automatic_preprocess_data(df, last_column_name)

            session.save_preprocessor(preprocessor)
            print(type(X_train))
            # Инициализация нейронной сети
            nn = NeuralNetwork(input_size=X_train.shape[1])
            print("pivot")

            for layer_config in session.model.parameters['layers']:
                #print(**layer_config)
                nn.add_layer(**layer_config)

            # Обучение
            best_loss = float('inf')
            best_weights = None

            for epoch in range(1, session.epochs + 1):
                print(f"epoch {epoch}")
                print(y_train)
                nn.train(X_train, y_train, learning_rate=session.learning_rate)

                # Расчет метрик
                output, _ = nn.forward(X_test)
                print(f"epoch {epoch}")
                loss = np.mean((output - y_test) ** 2)
                accuracy = np.mean(np.argmax(output, axis=1) == np.argmax(y_test, axis=1))

                # Сохранение параметров эпохи
                TrainingEpoch.objects.create(
                    session=session,
                    epoch_number=epoch,
                    loss=loss,
                    accuracy=accuracy,
                    learning_rate=session.learning_rate
                )

                # Сохранение лучшей модели
                if loss < best_loss:
                    best_loss = loss
                    best_weights = pickle.dumps(nn)
                    session.best_loss = best_loss
                    session.final_accuracy = accuracy

                # Обновление прогресса
                session.current_epoch = epoch
                session.progress = (epoch / session.epochs) * 100
                session.logs += f"Эпохи {epoch}: loss={loss:.4f}, accuracy={accuracy:.4f}\n"
                session.save()

            if best_weights:
                session.neural_network = best_weights
            session.status = 'completed'

        except Exception as e:
            print(f"error is {e}")
            if 'session' in locals():
                session.status = 'failed'
                session.logs += f"Error: {str(e)}\n"
                session.save()
        finally:
            if 'session' in locals():
                session.end_time = timezone.now()
                session.save()
            connection.close()

def start_training(session_id):
    """Запускает обучение в отдельном потоке"""
    thread = TrainingThread(session_id)
    thread.start()
    return thread