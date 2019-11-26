import numpy as np
import tensorflow as tf
from tensorflow import keras
import datetime
import prepare_data
from tensorflow.python.keras.callbacks import ModelCheckpoint
import os


def newCNNNetwork():
    # name = 'log_' + model_name + '_' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # tensBoard = keras.callbacks.TensorBoard(log_dir='log/'+name)
    # cb = ModelCheckpoint('models/' + r'{}.ml'.format(model_name), save_best_only=True, period=1)

    img_rows, img_cols = 6, 6
    number_of_categories = 4

    keras.backend.set_image_data_format('channels_last')

    # if keras.backend.image_data_format() == 'channels_first':
    input_shape = (img_rows, img_cols, 1)
    # else:
    #     input_shape = (img_rows,img_cols,1)

    # y_train = keras.utils.to_categorical(y_train, number_of_categories)

    model = keras.models.Sequential()

    model.add(keras.layers.Conv2D(128, (1, 2), input_shape=input_shape))
    model.add(keras.layers.Activation('relu'))
    model.add(keras.layers.MaxPooling2D(pool_size=(1, 1)))
    model.add(keras.layers.Dropout(0.2))
    #
    # model.add(keras.layers.Conv2D(128, (3, 3)))
    # model.add(keras.layers.Activation('relu'))
    # model.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))
    # model.add(keras.layers.Dropout(0.2))

    model.add(keras.layers.Flatten())

    model.add(keras.layers.Dense(512, activation='relu'))
    model.add(keras.layers.Dropout(0.3))

    model.add(keras.layers.Dense(512, activation='relu'))
    model.add(keras.layers.Dropout(0.3))

    model.add(keras.layers.Dense(number_of_categories, activation='softmax'))

    opt = keras.optimizers.Adam(decay=0.0001, lr=0.0001)
    model.compile(optimizer=opt, loss='binary_crossentropy', metrics=['accuracy'])
    #model.summary()
    return model
    # model.fit(x_train, y_train, epochs=2, batch_size=1, shuffle=True, validation_split=0.1, callbacks=[cb, tensBoard])
    # model.save(os.path.join('models', model_name + '.ml'))
    # #sess.close()
    # keras.backend.clear_session()


def check_gpu():
    sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))
    print('========================== Session =================================')
    print(sess)
    print('====================================================================')
    print('GPU is available: ' + str(tf.test.is_gpu_available()))
    print('GPU device name: ' + tf.test.gpu_device_name())


def model_summary(model_name):
    model = keras.models.load_model(os.path.join('models', model_name + '.ml'))
    model.summary()


def load_model(path):
    return keras.models.load_model(path)