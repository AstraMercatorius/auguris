import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense


class NNModel:
    def __init__(self, in_dim, n_classes, loss='categorical_crossentropy', epochs=32):
        model = Sequential([
            Dense(128, activation=keras.layers.LeakyReLU(negative_slope=0.01), input_dim=in_dim),
            Dense(64, activation=keras.layers.LeakyReLU(negative_slope=0.01)),
            Dense(32, activation=keras.layers.LeakyReLU(negative_slope=0.01)),
            Dense(n_classes, activation='softmax')
        ])
        model.compile(optimizer='adam',
                      loss=[loss],
                      metrics=[keras.metrics.CategoricalAccuracy()])
        self.model = model
        self.epochs = epochs

    def predict(self, pred_data):
        return np.argmax(self.model.predict(pred_data, verbose=0), axis=1) # type: ignore

    def load(self, filename):
        self.model = keras.models.load_model(filename, custom_objects={'LeakyReLU': keras.layers.LeakyReLU()})

