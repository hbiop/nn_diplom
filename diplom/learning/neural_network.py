import numpy as np


class NeuralNetwork:
    def __init__(self, input_size):
        self.layers = []
        self.input_size = input_size

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
        print("deltas")
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

    def predict(self, X):
        """Предсказание для новых данных."""
        output, _ = self.forward(X)
        return output