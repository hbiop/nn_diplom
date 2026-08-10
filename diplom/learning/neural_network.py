from typing import ClassVar

import numpy as np


class NeuralNetwork:
    """Небольшая полносвязная нейросеть с обучением методом backpropagation."""

    SUPPORTED_ACTIVATIONS: ClassVar[frozenset[str]] = frozenset({
        'sigmoid', 'relu', 'tanh', 'softmax', 'linear'
    })

    def __init__(self, input_size):
        if not isinstance(input_size, (int, np.integer)) or input_size < 1:
            raise ValueError('input_size должен быть положительным целым числом')

        self.input_size = int(input_size)
        self.layers = []

    def add_layer(self, size, activation='sigmoid'):
        if not isinstance(size, (int, np.integer)) or size < 1:
            raise ValueError('Размер слоя должен быть положительным целым числом')
        if activation not in self.SUPPORTED_ACTIVATIONS:
            raise ValueError(
                f'Неизвестная функция активации: {activation}. '
                f'Допустимые значения: {sorted(self.SUPPORTED_ACTIVATIONS)}'
            )

        previous_size = (
            self.input_size
            if not self.layers
            else self.layers[-1]['weights'].shape[1]
        )

        # He лучше подходит для ReLU, Xavier — для sigmoid/tanh и linear.
        if activation == 'relu':
            scale = np.sqrt(2.0 / previous_size)
        else:
            scale = np.sqrt(1.0 / previous_size)

        self.layers.append({
            'weights': np.random.randn(previous_size, int(size)) * scale,
            'biases': np.zeros(int(size), dtype=float),
            'activation': activation,
        })

    @staticmethod
    def _activate(z, activation):
        if activation == 'sigmoid':
            # Ограничиваем аргумент, чтобы избежать overflow в exp.
            return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))
        if activation == 'relu':
            return np.maximum(0.0, z)
        if activation == 'tanh':
            return np.tanh(z)
        if activation == 'softmax':
            shifted = z - np.max(z, axis=1, keepdims=True)
            exp_z = np.exp(shifted)
            return exp_z / np.sum(exp_z, axis=1, keepdims=True)
        if activation == 'linear':
            return z
        raise ValueError(f'Unknown activation: {activation}')

    @staticmethod
    def _activate_derivative(a, activation):
        if activation == 'sigmoid':
            return a * (1.0 - a)
        if activation == 'relu':
            return (a > 0).astype(float)
        if activation == 'tanh':
            return 1.0 - a ** 2
        if activation == 'linear':
            return np.ones_like(a)
        if activation == 'softmax':
            # Для softmax используется объединённый градиент CE ниже.
            return np.ones_like(a)
        raise ValueError(f'Unknown activation: {activation}')

    def forward(self, X):
        X = self._as_2d_array(X, 'X')
        if X.shape[1] != self.input_size:
            raise ValueError(
                f'Ожидалось {self.input_size} признаков, получено {X.shape[1]}'
            )
        if not self.layers:
            raise ValueError('Нейросеть должна содержать хотя бы один слой')

        activations = [X]
        for layer in self.layers:
            z = activations[-1] @ layer['weights'] + layer['biases']
            activations.append(self._activate(z, layer['activation']))
        return activations[-1], activations

    def loss(self, X_or_output, y, output_is_prediction=False):
        """Возвращает среднюю loss. Можно передать X или уже рассчитанный output."""
        y = self._as_2d_array(y, 'y')
        output = (
            self._as_2d_array(X_or_output, 'output')
            if output_is_prediction
            else self.predict(X_or_output)
        )
        if output.shape != y.shape:
            raise ValueError(f'Размер output {output.shape} не совпадает с y {y.shape}')

        activation = self.layers[-1]['activation']
        if activation == 'softmax':
            probabilities = np.clip(output, 1e-12, 1.0)
            return float(-np.mean(np.sum(y * np.log(probabilities), axis=1)))
        if activation == 'sigmoid':
            probabilities = np.clip(output, 1e-12, 1.0 - 1e-12)
            return float(-np.mean(
                y * np.log(probabilities) + (1.0 - y) * np.log(1.0 - probabilities)
            ))
        return float(np.mean((output - y) ** 2))

    def train(self, X, y, epochs=1, learning_rate=0.01,
              batch_size=32, shuffle=True, gradient_clip=5.0):
        """Обучает сеть и возвращает loss последней эпохи.

        Для многоклассовой классификации используйте последний слой softmax,
        для multilabel-классификации — sigmoid, для регрессии — linear.
        """
        X = self._as_2d_array(X, 'X')
        y = self._as_2d_array(y, 'y')
        if X.shape[0] != y.shape[0]:
            raise ValueError('Количество объектов в X и y должно совпадать')
        if epochs < 1 or learning_rate <= 0 or batch_size < 1:
            raise ValueError('epochs, learning_rate и batch_size должны быть положительными')
        if self.layers[-1]['weights'].shape[1] != y.shape[1]:
            raise ValueError('Размер выходного слоя должен совпадать с размером y')

        sample_count = X.shape[0]
        last_loss = 0.0
        for _ in range(int(epochs)):
            indices = np.random.permutation(sample_count) if shuffle else np.arange(sample_count)
            epoch_loss = 0.0

            for start in range(0, sample_count, int(batch_size)):
                batch_indices = indices[start:start + int(batch_size)]
                X_batch = X[batch_indices]
                y_batch = y[batch_indices]
                output, activations = self.forward(X_batch)
                epoch_loss += self.loss(output, y_batch, output_is_prediction=True) * len(batch_indices)

                output_activation = self.layers[-1]['activation']
                if output_activation in {'softmax', 'sigmoid'}:
                    deltas = [output - y_batch]
                else:
                    deltas = [
                        2.0 * (output - y_batch)
                        * self._activate_derivative(output, output_activation)
                    ]

                for layer_index in reversed(range(len(self.layers) - 1)):
                    next_layer = self.layers[layer_index + 1]
                    delta = (
                        deltas[-1] @ next_layer['weights'].T
                        * self._activate_derivative(
                            activations[layer_index + 1],
                            self.layers[layer_index]['activation'],
                        )
                    )
                    deltas.append(delta)
                deltas.reverse()

                for layer_index, layer in enumerate(self.layers):
                    grad_weights = activations[layer_index].T @ deltas[layer_index]
                    grad_biases = np.sum(deltas[layer_index], axis=0)
                    divisor = len(batch_indices)
                    grad_weights /= divisor
                    grad_biases /= divisor

                    if gradient_clip is not None:
                        norm = np.linalg.norm(grad_weights)
                        if norm > gradient_clip:
                            grad_weights *= gradient_clip / (norm + 1e-12)
                        bias_norm = np.linalg.norm(grad_biases)
                        if bias_norm > gradient_clip:
                            grad_biases *= gradient_clip / (bias_norm + 1e-12)

                    layer['weights'] -= learning_rate * grad_weights
                    layer['biases'] -= learning_rate * grad_biases

            last_loss = epoch_loss / sample_count

        return float(last_loss)

    def predict(self, X):
        output, _ = self.forward(X)
        return output

    @staticmethod
    def _as_2d_array(value, name):
        array = np.asarray(value, dtype=float)
        if array.ndim == 1:
            array = array.reshape(-1, 1)
        if array.ndim != 2:
            raise ValueError(f'{name} должен быть двумерным массивом')
        return array
