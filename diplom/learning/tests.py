import numpy as np
import pandas as pd
from django.test import TestCase

from learning.data_preprocessor import DataPreprocessor


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