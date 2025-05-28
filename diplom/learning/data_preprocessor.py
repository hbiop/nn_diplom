import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import numpy as np
from sklearn.utils import shuffle


class DataPreprocessor:
    data = None

    def __init__(self):
        self.data = None
        self.preprocessed_data = None
        self.preprocessed_label = None

    def get_predicted_label(self, prediction):
        class_index = np.argmax(prediction)
        return self.classes[class_index]

    def preprocess_data_for_predict(self, data):
        df = pd.DataFrame(data)
        print(f"pred s d{df.shape}")
        return self.preprocessor.transform(df)

    def automatic_preprocess_data(self,df_F, prediction_column):
        df = df_F
        df = shuffle(df)
        X = df.drop(prediction_column, axis=1)

        y = df[[prediction_column]]
        numeric = X.select_dtypes(include=['int64', 'float64']).columns.to_list()
        categorical = X.select_dtypes(include=['object', 'category', 'bool', 'datetime64']).columns.to_list()
        numeric_transformer = Pipeline(
            steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]
        )
        categorical_transformer = Pipeline(
            steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ]
        )
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric),
                ('cat', categorical_transformer, categorical)
            ]
        )
        self.preprocessed_data = self.preprocessor.fit_transform(X)

        self.preprocessed_label = categorical_transformer.fit_transform(y)
        self.label_encoder = OneHotEncoder(sparse_output=False)
        self.preprocessed_label = self.label_encoder.fit_transform(y.values.reshape(-1, 1))
        self.classes = self.label_encoder.categories_[0]
        return train_test_split(self.preprocessed_data, self.preprocessed_label, test_size=0.2, random_state=42)
