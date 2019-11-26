import numpy as np
from tensorflow import keras


def makeNew():
    inputs = [
        [0, 0],  # 0
        [0, 1],  # 1
        [1, 0],  # 1
        [1, 1]   # 0
    ]

    answers = [
        [0],
        [1],
        [1],
        [0]
    ]
    inputs = np.array(inputs)
    answers = np.array(answers)

    model = keras.Sequential()
    model.add(keras.layers.Dense(3, activation='sigmoid', input_shape=(2,)))
    model.add(keras.layers.Dense(1, activation="sigmoid",))

    optimizer = keras.optimizers.Adam(lr=0.1)
    model.compile(optimizer, loss='mean_squared_error', metrics=['accuracy'])
    model.fit(inputs, answers, batch_size=1, epochs=300, use_multiprocessing=False)
    keras.backend.clear_session()
    #model.save('model.h5')