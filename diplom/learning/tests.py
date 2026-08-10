import numpy as np
import pandas as pd
from django.test import TestCase

from learning.data_preprocessor import DataPreprocessor
from learning.secure_pickle import RestrictedUnpickler, dumps, loads

import io
import pickle


# Create your tests here.

class TestDataPreprocessing(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sample_data = {
            'numeric_feature': [1, 2, 3, 4, 5, np.nan, 7, 8, 9, 10],
            'categorical_feature': ['A', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B'],
            'bool_feature': [True, False, True, False, True, False, True, False, True, False],
            'target': ['cat', 'dog', 'cat', 'dog', 'bird', 'cat', 'dog', 'bird', 'cat', 'dog']
        }
        cls.df = pd.DataFrame(cls.sample_data)

    def test_signed_preprocessor_round_trip(self):
        processor = DataPreprocessor()
        processor.automatic_preprocess_data(self.df, 'target')

        restored = loads(dumps(processor))

        self.assertIsInstance(restored, DataPreprocessor)
        self.assertEqual(list(restored.classes), list(processor.classes))

    def test_tampered_artifact_is_rejected(self):
        artifact = bytearray(dumps({'safe': True}))
        artifact[-1] ^= 1

        with self.assertRaises(ValueError):
            loads(artifact)

    def test_unapproved_global_is_rejected(self):
        payload = pickle.dumps(ValueError('not allowed'))

        with self.assertRaises(pickle.UnpicklingError):
            RestrictedUnpickler(io.BytesIO(payload)).load()

    def test_automatic_preprocess_data(self):
        processor = DataPreprocessor()
        X_train, X_test, y_train, y_test = processor.automatic_preprocess_data(
            df_F=self.df,
            prediction_column='target'
        )

        self.assertEqual(len(X_train), len(y_train))
        self.assertEqual(len(X_test), len(y_test))
        self.assertEqual(X_train.shape[1], X_test.shape[1])

        self.assertTrue(hasattr(processor, 'preprocessor'))
        self.assertTrue(hasattr(processor, 'label_encoder'))

        original_categorical_cols = 2
        unique_categories = len(set(self.sample_data['categorical_feature']))
        unique_bool = 2
        expected_onehot_features = unique_categories + unique_bool
        self.assertGreater(X_train.shape[1], original_categorical_cols)

        self.assertEqual(len(processor.classes), len(set(self.sample_data['target'])))