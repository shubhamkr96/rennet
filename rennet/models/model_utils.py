#!/usr/bin/python

from __future__ import division, print_function
import os
import sys
rennetroot = os.environ['RENNET_ROOT']
sys.path.append(rennetroot)

import numpy as np
import glob
import h5py
from keras.utils.np_utils import to_categorical
from sklearn.metrics import confusion_matrix

import keras.layers as kl
import keras.optimizers as ko
from keras.models import Sequential
import keras.callbacks as kc


def get_gertv_data():
    workingdir = os.path.join(rennetroot, 'data', 'working')
    proj = 'gertv1000-utt'
    dataset = 'AudioMining'
    picklesdir = os.path.join(workingdir, proj, dataset, 'train', 'pickles')

    data_fps = glob.glob(os.path.join(picklesdir, '20161019*.hdf5'))
    print()
    print("{:/>90}//".format(" TRAINING SOURCE FILES "))
    print(*list(enumerate(data_fps)), sep='\n')

    trn_X = []
    trn_y = []
    for f in data_fps:
        ff = h5py.File(f, 'r')
        trn_X.append(ff['data'][()])
        trn_y.append(ff['labels'][()])

    trn_X = np.concatenate(trn_X)
    trn_y = np.concatenate(trn_y)

    trntilli = int(0.90 * trn_y.shape[0])

    val_X = trn_X[trntilli:, :]
    val_y = trn_y[trntilli:]

    trn_X = trn_X[:trntilli, :]
    trn_y = trn_y[:trntilli]

    nclasses = 2
    nfeatures = trn_X.shape[1]
    trn_Y = to_categorical(trn_y, nb_classes=nclasses)
    val_Y = to_categorical(val_y, nb_classes=nclasses)
    del trn_y

    print('Training: {}, {}'.format(trn_X.shape, trn_Y.shape))
    print('Validation: {}, {}'.format(val_X.shape, val_Y.shape))

    return {
        'train_X': trn_X,
        'train_Y': trn_Y,
        'validation_X': val_X,
        'validation_Y': val_Y,
        'validation_y': val_y,
        'nclasses': nclasses,
        'nfeatures': nfeatures,
        'class_counts': trn_Y.sum(axis=0)
    }


def print_confusion(y_true, y_pred):
    conx = confusion_matrix(y_true, y_pred)
    conx = conx.astype(np.float) / conx.sum(axis=1)[:, np.newaxis]

    print()
    print("{:/>90}//".format(' CONFUSION MATRIX '))
    print(conx)
    print()


def model_00_batchnrm_Ndense_softmax(nfeatures, nclasses, denselayers,
                                     dropouts):
    model = Sequential()
    model.add(kl.InputLayer(input_shape=(nfeatures, )))
    model.add(kl.BatchNormalization())

    for i in range(len(denselayers)):
        od, act = denselayers[i]
        dp = dropouts[i]

        model.add(kl.Dense(od, activation=act))
        model.add(kl.Dropout(dp))

    model.add(kl.Dense(nclasses, activation='softmax'))

    return model


def model_00_Ndense_softmax(nfeatures, nclasses, denselayers, dropouts):
    model = Sequential()
    model.add(kl.InputLayer(input_shape=(nfeatures, )))

    for i in range(len(denselayers)):
        od, act = denselayers[i]
        dp = dropouts[i]

        model.add(kl.Dense(od, activation=act))
        model.add(kl.Dropout(dp))

    model.add(kl.Dense(nclasses, activation='softmax'))
    return model


def gertv_compile_train_eval(model,
                             optimizer,
                             callbacks,
                             batchsize,
                             nepochs,
                             class_weights=1,
                             normalize=False,
                             verbose=2):

    dataset = get_gertv_data()
    trn_X = dataset['train_X']
    val_X = dataset['validation_X']

    if normalize:
        trnxm = np.mean(trn_X, axis=0)
        trnxs = np.std(trn_X, axis=0)

        trn_X = (trn_X - trnxm[:, np.newaxis]) / trnxs[:, np.newaxis]
        val_X = (val_X - trnxm[:, np.newaxis]) / trnxs[:np.newaxis]

        if verbose > 0:
            print()
            print("Mean:\n{}".format(trnxm))
            print("Stdv:\n{}".format(trnxs))
            print()

    trn_Y = dataset['train_Y']
    val_Y = dataset['validation_Y']

    if verbose > 0:
        print()
        model.summary()
        print()

    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['categorical_accuracy'])


    if isinstance(class_weights, int) or (isinstance(class_weights, bool) and
                                          not class_weights):
        class_weights = dict.fromkeys(range(dataset['nclasses']))
        for k in class_weights:
            class_weights[k] = 1

    elif isinstance(class_weights, bool) and class_weights:
        clscounts = dataset['class_counts']
        clsws = sum(clscounts) / clscounts

        class_weights = dict.fromkeys(range(len(clsws)))
        for k in class_weights:
            class_weights[k] = clsws[k]

    
    model.fit(trn_X,
              trn_Y,
              validation_data=(val_X, val_Y),
              class_weight=class_weights,
              shuffle=True,
              batch_size=batchsize,
              nb_epoch=nepochs,
              callbacks=callbacks,
              verbose=verbose)

    if verbose > 0:
        preds = model.predict_classes(val_X, verbose=1)
        print_confusion(dataset['validation_y'], preds)
