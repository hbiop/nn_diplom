import numpy as np
import pandas as pd

from learning.data_preprocessor import DataPreprocessor


class NeuralNetwork:
    def __init__(self, input_size):
        self.layers = []
        self.input_size = input_size
        print("pivot")

    def add_layer(self, size, activation='sigmoid'):
        if not self.layers:
            layer = {
                'weights': np.random.randn(self.input_size, size) * 0.1,
                'biases': np.zeros(size),
                'activation': activation
            }
        else:
            prev_size = self.layers[-1]['weights'].shape[1]
            layer = {
                'weights': np.random.randn(prev_size, size) * 0.1,
                'biases': np.zeros(size),
                'activation': activation
            }
        self.layers.append(layer)

    def forward(self, X):
        activations = [X]
        for layer in self.layers:
            z = np.dot(activations[-1], layer['weights']) + layer['biases']
            a = self._activate(z, layer['activation'])
            activations.append(a)
        return activations[-1], activations

    @staticmethod
    def _activate(z, activation):
        if activation == 'sigmoid':
            return 1 / (1 + np.exp(-z))
        elif activation == 'relu':
            return np.maximum(0, z)
        elif activation == 'tanh':
            return np.tanh(z)
        return z

    @staticmethod
    def _activate_derivative(a, activation):
        if activation == 'sigmoid':
            return a * (1 - a)
        elif activation == 'relu':
            return (a > 0).astype(float)
        elif activation == 'tanh':
            return 1 - a ** 2
        return np.ones_like(a)

    def train(self, X, y, epochs=1000, learning_rate=0.1):
        #for epoch in range(epochs):
        output, activations = self.forward(X)

        error = output - y
        deltas = [error * self._activate_derivative(output, self.layers[-1]['activation'])]

        for i in reversed(range(len(self.layers) - 1)):
            delta = np.dot(deltas[-1], self.layers[i + 1]['weights'].T) * \
                    self._activate_derivative(activations[i + 1], self.layers[i]['activation'])
            deltas.append(delta)
        deltas.reverse()

        # Обновление весов и смещений
        for i in range(len(self.layers)):
            grad_weights = np.dot(activations[i].T, deltas[i])
            grad_biases = np.sum(deltas[i], axis=0)
            self.layers[i]['weights'] -= learning_rate * grad_weights
            self.layers[i]['biases'] -= learning_rate * grad_biases

        # if epoch % 100 == 0:
        #     loss = np.mean(error ** 2)
        #     print(f'Epoch {epoch}, Loss: {loss:.4f}')

    def predict(self, X):
        """Предсказание для новых данных."""
        output, _ = self.forward(X)
        return output

if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    columns = ['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm', 'Species']
    df = pd.read_excel('D:\\need\\python\\data_service\\data_sets\\iris\\Iris.xlsx')
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    encoder = OneHotEncoder(sparse_output=False)
    y = encoder.fit_transform(df[['Species']])

    X = df.drop('Species', axis=1).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    np.random.seed(42)
    nn = NeuralNetwork(input_size=X_train.shape[1])

    nn.add_layer(size=10, activation='relu')
    nn.add_layer(size=y_train.shape[1], activation='sigmoid')  # Выходной слой

    epochs = 1000
    learning_rate = 0.01

    for epoch in range(epochs):
        nn.train(X_train, y_train, epochs=1, learning_rate=learning_rate)
        if epoch % 100 == 0:
            pred = nn.predict(X_train)
            loss = np.mean((pred - y_train) ** 2)
            print(f'Epoch {epoch}, Loss: {loss:.4f}')


    def accuracy(y_true, y_pred):
        return np.mean(np.argmax(y_true, axis=1) == np.argmax(y_pred, axis=1))


    y_pred_train = nn.predict(X_train)
    y_pred_test = nn.predict(X_test)


    def decode_onehot(onehot, encoder):
        a = encoder.inverse_transform(onehot).flatten()
        return a


    y_test_labels = decode_onehot(y_test, encoder)
    y_pred_labels = decode_onehot(y_pred_test, encoder)

    print("\nПримеры предсказаний на тестовой выборке:")
    print(f"{'Предсказание':<20} {'Фактический класс':<20} {'Верно?':<10}")
    print("-" * 50)
    for i in range(min(10, len(y_test_labels))):  # Первые 10 примеров
        pred = y_pred_labels[i]
        true = y_test_labels[i]
        correct = "✓" if pred == true else "✗"
        print(f"{pred:<20} {true:<20} {correct:<10}")

    test_acc = accuracy(y_test, y_pred_test)
    print(f'\nTest Accuracy: {test_acc:.2%}')

