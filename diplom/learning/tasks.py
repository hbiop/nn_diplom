import logging

import numpy as np
import pandas as pd
from celery import shared_task
from django.db import close_old_connections, transaction

from .data_preprocessor import DataPreprocessor
from .models import TrainingEpoch, TrainingSession
from .neural_network import NeuralNetwork
from .secure_pickle import dumps as secure_dumps

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='learning.train_session')
def train_session(self, session_id):
    """Train one session in a Celery worker and persist progress in the DB."""
    close_old_connections()
    session = None

    try:
        with transaction.atomic():
            session = TrainingSession.objects.select_for_update().select_related(
                'dataset', 'model'
            ).get(pk=session_id)

            if session.status != 'pending':
                return {'status': session.status, 'session_id': session_id}

            session.status = 'running'
            session.current_epoch = 0
            session.progress = 0
            session.logs = ''
            session.save(update_fields=[
                'status', 'current_epoch', 'progress', 'logs'
            ])

        if session.dataset.file_type == 'CSV':
            df = pd.read_csv(session.dataset.file.path)
        elif session.dataset.file_type == 'XLSX':
            df = pd.read_excel(session.dataset.file.path)
        else:
            raise ValueError(f'Unsupported dataset type: {session.dataset.file_type}')

        preprocessor = DataPreprocessor()
        last_column_name = df.columns[-1]
        X_train, X_test, y_train, y_test = preprocessor.automatic_preprocess_data(
            df, last_column_name
        )
        session.save_preprocessor(preprocessor)

        nn = NeuralNetwork(input_size=X_train.shape[1])
        for layer_config in session.model.parameters['layers']:
            nn.add_layer(**layer_config)

        best_loss = float('inf')
        best_weights = None

        for epoch in range(1, session.epochs + 1):
            session.refresh_from_db(fields=['status'])
            if session.status == 'cancelled':
                return {'status': 'cancelled', 'session_id': session_id}

            nn.train(
                X_train,
                y_train,
                epochs=1,
                learning_rate=session.learning_rate,
                batch_size=min(32, len(X_train)),
            )
            output = nn.predict(X_test)
            loss = nn.loss(output, y_test, output_is_prediction=True)
            accuracy = float(
                np.mean(np.argmax(output, axis=1) == np.argmax(y_test, axis=1))
            )

            TrainingEpoch.objects.update_or_create(
                session=session,
                epoch_number=epoch,
                defaults={
                    'loss': loss,
                    'accuracy': accuracy,
                    'learning_rate': session.learning_rate,
                },
            )

            if loss < best_loss:
                best_loss = loss
                best_weights = secure_dumps(nn)
                session.best_loss = best_loss
                session.final_accuracy = accuracy

            session.current_epoch = epoch
            session.progress = (epoch / session.epochs) * 100
            session.logs += (
                f'Эпоха {epoch}: loss={loss:.4f}, accuracy={accuracy:.4f}\n'
            )
            session.save(update_fields=[
                'current_epoch', 'progress', 'logs',
                'best_loss', 'final_accuracy',
            ])
            self.update_state(
                state='PROGRESS',
                meta={'current_epoch': epoch, 'progress': session.progress},
            )

        session.refresh_from_db(fields=['status'])
        if session.status == 'cancelled':
            return {'status': 'cancelled', 'session_id': session_id}

        session.neural_network = best_weights
        session.status = 'completed'
        session.progress = 100
        session.save(update_fields=[
            'neural_network', 'status', 'progress', 'best_loss', 'final_accuracy'
        ])
        return {'status': 'completed', 'session_id': session_id}

    except TrainingSession.DoesNotExist:
        logger.warning('Training session %s does not exist', session_id)
        raise
    except Exception as exc:
        logger.exception('Training failed for session %s', session_id)
        if session is not None:
            session.status = 'failed'
            session.logs = f'{session.logs}Ошибка: {exc}\n'
            session.save(update_fields=['status', 'logs'])
        raise
    finally:
        close_old_connections()


def start_training(session_id):
    """Queue training and return the Celery AsyncResult."""
    return train_session.delay(session_id)
