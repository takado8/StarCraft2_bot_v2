import numpy as np
import tensorflow as tf
from tensorflow import keras
import datetime
import os
import constants


def newCNNNetwork():
    # img_rows, img_cols = 64, 64
    number_of_categories = 6

    keras.backend.set_image_data_format('channels_last')

    # if keras.backend.image_data_format() == 'channels_first':
    input_shape = constants.INPUT_SHAPE    # (img_rows, img_cols, 3)
    # else:
    #     input_shape = (img_rows,img_cols,1)

    # y_train = keras.utils.to_categorical(y_train, number_of_categories)

    model = keras.models.Sequential()

    model.add(keras.layers.Conv2D(64, (3, 3), input_shape=input_shape))
    model.add(keras.layers.Activation('relu'))
    model.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))
    model.add(keras.layers.Dropout(0.2))
    #
    # model.add(keras.layers.Conv2D(128, (3, 3)))
    # model.add(keras.layers.Activation('relu'))
    # model.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))
    # model.add(keras.layers.Dropout(0.2))

    model.add(keras.layers.Flatten())

    model.add(keras.layers.Dense(256, activation='relu'))
    model.add(keras.layers.Dropout(0.3))

    model.add(keras.layers.Dense(512, activation='relu'))
    model.add(keras.layers.Dropout(0.3))

    model.add(keras.layers.Dense(number_of_categories, activation='linear'))

    opt = keras.optimizers.Adam(decay=0.00000, lr=0.0001)
    model.compile(optimizer=opt, loss='mse', metrics=['accuracy'])   #binary_crossentropy
    #model.summary()
    return model
    # model.fit(x_train, y_train, epochs=2, batch_size=1, shuffle=True, validation_split=0.1, callbacks=[cb, tensBoard])
    # model.save(os.path.join('models', model_name + '.ml'))
    # #sess.close()
    # keras.backend.clear_session()



def model_summary(model_name):
    model = keras.models.load_model(os.path.join('models', model_name + '.ml'))
    model.summary()


def load_model(path):
    return keras.models.load_model(path)
