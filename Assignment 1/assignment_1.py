# -*- coding: utf-8 -*-
"""Assignment-1_notebook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KzR6g9UAnaRe1F3hD6EHT-_RALOIVmsh

Import and setup some auxiliary functions
"""

from tensorflow.contrib.learn.python.learn.datasets.mnist import read_data_sets
import numpy as np
import timeit
from collections import OrderedDict
from pprint import pformat
import tensorflow as tf


def compute_score(acc, min_thres, max_thres):
    if acc <= min_thres:
        base_score = 0.0
    elif acc >= max_thres:
        base_score = 100.0
    else:
        base_score = float(acc - min_thres) / (max_thres - min_thres) \
            * 100
    return base_score


def run(algorithm, x_train, y_train, x_test, y_test):
    print('Running...')
    start = timeit.default_timer()
    np.random.seed(0)
    predicted_y_test = algorithm(x_train, y_train, x_test)
    np.random.seed()
    stop = timeit.default_timer()
    run_time = stop - start

    correct_predict = (y_test
                       == predicted_y_test).astype(np.int32).sum()
    incorrect_predict = len(y_test) - correct_predict
    accuracy = float(correct_predict) / len(y_test)

    print('Correct Predict: {}/{} total \tAccuracy: {:5f} \tTime: {:2f}'.format(correct_predict,
            len(y_test), accuracy, run_time))
    return (correct_predict, accuracy, run_time)

"""TODO: Implement knn here"""

def knn(x_train, y_train, x_test):
    """
    x_train: 60000 x 784 matrix: each row is a flattened image of an MNIST digit
    y_train: 60000 vector: label for x_train
    x_test: 5000 x 784 testing images
    return: predicted y_test which is a 5000 vector
    """
    # TODO: Implement knn here
    g = tf.Graph()
    with g.as_default() as g:
      x_1 = tf.placeholder(dtype = tf.float32)
      # calculate L2 distance
      # minus operator implicitly broadcasts matrix?
      square = tf.pow((x_1 - x_train), 2)
      # row vector form 
      col_sum = tf.reduce_sum(square,1)
      distance = tf.sqrt(col_sum)
      # top_k returns the largest values, so reverse the values to return the smallest values 
      closest = tf.negative(distance)
      # _, returns only indices 
      indices = tf.nn.top_k(closest, k=3)[1]
      # compare the index values to the training values      
      labels = tf.gather(y_train, indices)
      
    y_test = np.zeros(x_test.shape[0])
    count = 0
    with tf.Session(graph=g) as sess:
      sess.run(tf.global_variables_initializer())
      for point in x_test: 
        gather1 = sess.run(labels, feed_dict={x_1: point})
        # get a count of the occurrences of each value
        occurrences = np.bincount(gather1)
        # grab the most occurring number
        mode = np.argmax(occurrences)
        # update y_test values to reflect the labels 
        y_test[count] = mode
        count += 1 

    return y_test

"""Main loop. You can only run this after filling the knn function above"""

min_thres=0.84
max_thres=0.94

mnist = read_data_sets('data', one_hot=False)
result = [OrderedDict(first_name='Insert your First name here',
          last_name='Insert your Last name here')]

(x_train, y_train) = (mnist.train._images, mnist.train._labels)
(x_valid, y_valid) = (mnist.test._images, mnist.test.labels)

# You may want to use a smaller training set to save time when debugging
# i.e.: Put something like:
(x_train, y_train) = (x_train[:55000], y_train[:55000])

# For this assignment, we only test on the first 1000 samples of the test set
(x_valid, y_valid) = (x_valid[:1000], y_valid[:1000])

print("Dimension of dataset: ")
print("Train:", x_train.shape, y_train.shape, "\nTest:", x_valid.shape, y_valid.shape)

(correct_predict, accuracy, run_time) = run(knn, x_train, y_train, x_valid, y_valid)
score = compute_score(accuracy, min_thres, max_thres)
result = OrderedDict(correct_predict=correct_predict,
                     accuracy=accuracy, score=score,
                     run_time=run_time)
    
with open('result.txt', 'w') as f:
    f.writelines(pformat(result, indent=4))

print(pformat(result, indent=4))

