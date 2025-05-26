import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import numpy as np

class DataPreprocessor:
    def __init__(self):
        self.preprocessor = None
        self.label_encoder = None
        self.classes = None
        self.feature_names = None
        self.target_column = None

    def preprocess_data(self, data, target_column):
        """Основной метод предобработки данных"""
        try:
            df = pd.DataFrame(data)
            self.target_column = target_column

            # Проверка наличия целевой колонки
            if target_column not in df.columns:
                raise ValueError(f"Целевая колонка '{target_column}' не найдена в данных")

            # Разделение на признаки и целевую переменную
            X = df.drop(target_column, axis=1)
            y = df[[target_column]]

            # Определение типов признаков
            numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
            categorical_features = X.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

            # Проверка на отсутствие признаков
            if not numeric_features and not categorical_features:
                raise ValueError("Не найдено признаков для обработки")

            # Создание пайплайнов для разных типов признаков
            numeric_transformer = Pipeline([
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])

            categorical_transformer = Pipeline([
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])

            # Создание ColumnTransformer
            self.preprocessor = ColumnTransformer([
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])

            # Преобразование признаков
            X_processed = self.preprocessor.fit_transform(X)
            self.feature_names = self._get_feature_names()

            # Преобразование целевой переменной
            self.label_encoder = OneHotEncoder()
            y_processed = self.label_encoder.fit_transform(y.values.reshape(-1, 1))
            self.classes = self.label_encoder.categories_[0]

            # Перемешивание и разделение данных
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y_processed, test_size=0.2, random_state=42
            )

            return X_train, X_test, y_train, y_test

        except Exception as e:
            raise ValueError(f"Ошибка предобработки данных: {str(e)}")

    def _get_feature_names(self):
        """Получает имена признаков после преобразования"""
        feature_names = []

        for name, trans, columns in self.preprocessor.transformers_:
            if name == 'num':
                feature_names.extend(columns)
            elif name == 'cat':
                # Для one-hot кодирования добавляем имена категорий
                encoder = trans.named_steps['onehot']
                categories = encoder.categories_
                for i, col in enumerate(columns):
                    for cat in categories[i]:
                        feature_names.append(f"{col}_{cat}")

        return feature_names

    def preprocess_new_data(self, data):
        """Предобработка новых данных с использованием обученного преобразователя"""
        if self.preprocessor is None:
            raise ValueError("Преобразователь не обучен. Сначала вызовите preprocess_data")

        df = pd.DataFrame(data)
        return self.preprocessor.transform(df)

    def get_predicted_label(self, prediction):
        """Преобразует предсказание в текстовую метку"""
        if self.label_encoder is None:
            raise ValueError("Кодировщик меток не обучен")

        class_index = np.argmax(prediction)
        return self.classes[class_index]