# -*- coding: utf-8 -*-
"""assignment_9_eval.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iti0z5qx7IvMXkGJEaop1dA4xywDw1vQ
"""

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from skimage.draw import polygon


def compute_classification_acc(pred, gt):
  # pred and gt are both
  assert pred.shape == gt.shape
  return (pred == gt).astype(int).sum() / gt.size
    
    
def compute_iou(b_pred,b_gt):
  # b_pred: predicted bounding boxes, shape=(n,2,4)
  # b_gt: ground truth bounding boxes, shape=(n,2,4)
    
  n = np.shape(b_gt)[0]
  L_pred = np.zeros((64,64))
  L_gt = np.zeros((64,64))
  iou = 0.0
  for i in range(n):
    for b in range(2):
      rr, cc = polygon([b_pred[i,b,0],b_pred[i,b,0],b_pred[i,b,2],b_pred[i,b,2]],
                   [b_pred[i,b,1],b_pred[i,b,3],b_pred[i,b,3],b_pred[i,b,1]],[64,64])
      L_pred[rr,cc] = 1

      rr, cc = polygon([b_gt[i,b,0],b_gt[i,b,0],b_gt[i,b,2],b_gt[i,b,2]],
                      [b_gt[i,b,1],b_gt[i,b,3],b_gt[i,b,3],b_gt[i,b,1]],[64,64])
      L_gt[rr,cc] = 1

      iou += (1.0/(2*n))*(np.sum((L_pred+L_gt)==2)/np.sum((L_pred+L_gt)>=1))

      L_pred[:,:] = 0
      L_gt[:,:] = 0
    
  return iou


def evaluation(pred_class, pred_bboxes, prefix="valid"):
  # pred_class: Your predicted labels for the 2 digits, shape [N, 2]
  # pred_bboxes: Your predicted bboxes for 2 digits, shape [N, 2, 4]
  gt_class = np.load(prefix + "_Y.npy")
  gt_bboxes = np.load(prefix + "_bboxes.npy")
  acc = compute_classification_acc(pred_class, gt_class)
  iou = compute_iou(pred_bboxes, gt_bboxes)
  print(f"Classification Acc: {acc}")
  print(f"BBoxes IOU: {iou}")
  
# to test the test set  
def evaluation_test(pred_class, pred_bboxes, prefix="test"):
  # pred_class: Your predicted labels for the 2 digits, shape [N, 2]
  # pred_bboxes: Your predicted bboxes for 2 digits, shape [N, 2, 4]
  gt_class = np.load(prefix + "_Y.npy")
  gt_bboxes = np.load(prefix + "_bboxes.npy")
  acc = compute_classification_acc(pred_class, gt_class)
  iou = compute_iou(pred_bboxes, gt_bboxes)
  print(f"Classification Acc: {acc}")
  print(f"BBoxes IOU: {iou}")

class DatasetIterator:
    def __init__(self, x, y, bb, batch_size):
        assert len(x) == len(y)
        self.x = x
        self.y = y
        self.bb = bb
        self.b_sz = batch_size
        self.b_pt = 0
        self.d_sz = len(x)
        self.idx = None
        self.randomize()

    def randomize(self):
        self.idx = np.random.permutation(self.d_sz)
        self.b_pt = 0

    def next_batch(self):
        start = self.b_pt
        end = self.b_pt + self.b_sz
        idx = self.idx[start:end]
        x = self.x[idx]
        y = self.y[idx]
        bb = self.bb[idx]

        self.b_pt += self.b_sz
        if self.b_pt >= self.d_sz:
            self.randomize()

        return x, y, bb

def cls_net(x, isTrain):    
    
    # Hyperparameters
    mu = 0
    sigma = 0.1
    # output size = (N - F) / stride + 1
    
    # Layer 1: Convolutional. Input = 64x64x1.
    conv1 = tf.layers.conv2d(inputs=x,filters=16, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv1 = tf.layers.conv2d(inputs=conv1,filters=16, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv1 = tf.layers.batch_normalization(conv1, training=isTrain)
    
    # half after every max pool 
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)
    
    conv2 = tf.layers.conv2d(inputs=pool1,filters=32, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv2 = tf.layers.conv2d(inputs=conv2,filters=32, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv2 = tf.layers.batch_normalization(conv2, training=isTrain)
    
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

    conv3 = tf.layers.conv2d(inputs=pool2,filters=64, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv3 = tf.layers.conv2d(inputs=conv3,filters=64, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv3 = tf.layers.batch_normalization(conv3, training=isTrain)
    
    pool3 = tf.layers.max_pooling2d(inputs=conv3, pool_size=[2, 2], strides=2)
    
    conv4 = tf.layers.conv2d(inputs=pool3,filters=128, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv4 = tf.layers.conv2d(inputs=conv4,filters=128, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv4 = tf.layers.batch_normalization(conv4, training=isTrain)

    pool4 = tf.layers.max_pooling2d(inputs=conv4, pool_size=[2, 2], strides=2)

    fc0 = tf.contrib.layers.flatten(pool4)
    
    # FC layer
    fc1_W = tf.Variable(tf.truncated_normal(shape=(2048, 1024), mean = mu, stddev = sigma), name='fc1_W')
    fc1_b = tf.Variable(tf.zeros(1024), name='fc1_b')
    fc1   = tf.matmul(fc0, fc1_W) + fc1_b
    
    # Dropout layer, probability 0.8
    dropout = 0.8
    DropMask = (tf.to_float(tf.random_uniform((1,1024))<dropout))/dropout
    fc1 = tf.cond(isTrain, lambda: fc1*DropMask, lambda: fc1)
    fc1 = tf.layers.batch_normalization(fc1,training=isTrain)
    
    # FC layer, output 20, because we need to get 2 digits
    fc2_W = tf.Variable(tf.truncated_normal(shape=(1024, 20), mean = mu, stddev = sigma), name='fc2_W')
    fc2_b = tf.Variable(tf.zeros(20), name='fc2_b')
    label_logits   = tf.matmul(fc1, fc2_W) + fc2_b
    
    return label_logits
    
def bb_net(x, isTrain):    
  
    # Hyperparameters
    mu = 0
    sigma = 0.1
    
    # Layer 1: Convolutional. Input = 64x64x1.
    conv1 = tf.layers.conv2d(inputs=x,filters=16, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv1 = tf.layers.conv2d(inputs=conv1,filters=16, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv1 = tf.layers.batch_normalization(conv1, training=isTrain)
    
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)
    
    conv2 = tf.layers.conv2d(inputs=pool1,filters=32, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv2 = tf.layers.conv2d(inputs=conv2,filters=32, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv2 = tf.layers.batch_normalization(conv2, training=isTrain)
    
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

    conv3 = tf.layers.conv2d(inputs=pool2,filters=64, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv3 = tf.layers.conv2d(inputs=conv3,filters=64, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv3 = tf.layers.batch_normalization(conv3, training=isTrain)
    
    pool3 = tf.layers.max_pooling2d(inputs=conv3, pool_size=[2, 2], strides=2)
    
    conv4 = tf.layers.conv2d(inputs=pool3,filters=128, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv4 = tf.layers.conv2d(inputs=conv4,filters=128, kernel_size=[3, 3], padding="SAME", activation=tf.nn.relu)
    conv4 = tf.layers.batch_normalization(conv4, training=isTrain)
    
    pool4 = tf.layers.max_pooling2d(inputs=conv4, pool_size=[2, 2], strides=2)

    # flatten before FC
    fc0 = tf.contrib.layers.flatten(pool4)
    
    fc1_W = tf.Variable(tf.truncated_normal(shape=(2048, 1024), mean = mu, stddev = sigma), name='fc1_W')
    fc1_b = tf.Variable(tf.zeros(1024), name='fc1_b')
    fc1   = tf.matmul(fc0, fc1_W) + fc1_b
    
    # Dropout layer
    dropout = 0.8
    DropMask = (tf.to_float(tf.random_uniform((1,1024))<dropout))/dropout
    fc1 = tf.cond(isTrain, lambda: fc1*DropMask, lambda: fc1)
    fc1 = tf.layers.batch_normalization(fc1,training=isTrain)
    
    # FC layer, output 8 
    fc2_W = tf.Variable(tf.truncated_normal(shape=(1024, 8), mean = mu, stddev = sigma), name='fc2_W')
    fc2_b = tf.Variable(tf.zeros(8), name='fc2_b')
    bb_logits   = tf.matmul(fc1, fc2_W) + fc2_b
    
    return bb_logits

def cls_train():

  tf.reset_default_graph()

  EPOCHS = 100
  batches = 100
  lr = 0.002  
  
  x = tf.placeholder(tf.float32, (None, 64, 64, 1))
  y = tf.placeholder(tf.float32, (None, 20))
  
  train = tf.placeholder(tf.bool)
  
  cls_logits = cls_net(x, train)
  
  # sigmoid vs softmax
  loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits = cls_logits, labels = y))

  optimizer = tf.train.AdamOptimizer(learning_rate = lr)
  
  grads_and_vars = optimizer.compute_gradients(loss, tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES))
  
  update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS) # to take care of Dropout layer
  with tf.control_dependencies(update_ops):
    training_operation = optimizer.apply_gradients(grads_and_vars)
    
  with tf.Session() as sess:

      sess.run(tf.global_variables_initializer())

      x_train = np.load("train_X.npy")
      # 55000,4096 -> 55000,64,64,1
      x_train = np.reshape(x_train, [55000, 64, 64, 1])
      y_train = np.load("train_Y.npy")
      y_train = tf.one_hot(y_train, 10)
      y_train = tf.contrib.layers.flatten(y_train)
      y_train = y_train.eval()
      bb_train = np.load("train_bboxes.npy")

      dataset_iterator = DatasetIterator(x_train, y_train, bb_train, batches)

      x_valid = np.load("valid_X.npy")
      x_valid = np.reshape(x_valid, [5000, 64, 64, 1])
      y_valid = np.load("valid_Y.npy")
           
      saver = tf.train.Saver()        
      # training on 55k training set    
      for i in range(EPOCHS):
        for j in range(batches):
          x_batch, y_batch, bb_batch = dataset_iterator.next_batch()
          sess.run(training_operation, feed_dict = {x: x_batch, y: y_batch, train: True})
              
      # save the model after training
      path = saver.save(sess, "./cls_model.dat")
      
  return 

def bb_train():

  tf.reset_default_graph()

  EPOCHS = 50
  batches = 100
  lr = 0.002  
  
  x = tf.placeholder(tf.float32, (None, 64, 64, 1))
  y = tf.placeholder(tf.float32, (None, 8)) 
  
  train = tf.placeholder(tf.bool)
  
  bb_logits = bb_net(x, train)
  
  # MSE is the loss function we should use
  loss = tf.reduce_mean(tf.losses.mean_squared_error(predictions = bb_logits, labels = y)) 
  
  optimizer = tf.train.AdamOptimizer(learning_rate = lr)

  grads_and_vars = optimizer.compute_gradients(loss, tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES))
  
  update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS) # to take care of Dropout layer
  with tf.control_dependencies(update_ops):
    training_operation = optimizer.apply_gradients(grads_and_vars)
    
  with tf.Session() as sess:

      sess.run(tf.global_variables_initializer())

      x_train = np.load("train_X.npy")
      x_train = np.reshape(x_train, [55000, 64, 64, 1])
      y_train = np.load("train_Y.npy")
      
      x_valid = np.load("valid_X.npy")
      x_valid = np.reshape(x_valid, [5000, 64, 64, 1])
      bb_valid = np.load("valid_bboxes.npy")
      
      bb_train = np.load("train_bboxes.npy")
      bb_train = tf.contrib.layers.flatten(bb_train)
      bb_train = bb_train.eval()
      dataset_iterator = DatasetIterator(x_train, y_train, bb_train, batches)
      
      saver = tf.train.Saver()
      
      for i in range(EPOCHS):
        for j in range(batches):
          x_batch, y_batch, bb_batch = dataset_iterator.next_batch()
          sess.run(training_operation, feed_dict = {x: x_batch, y: bb_batch, train: True})
        
      path = saver.save(sess, "./bb_model.dat")
  
  return

def cls_test():
  
  tf.reset_default_graph()
  
  x = tf.placeholder(tf.float32, (None, 64, 64, 1))
  y = tf.placeholder(tf.float32, (None, 20)) 
  train = tf.placeholder(tf.bool)
  cls_logits = cls_net(x, train)  

  with tf.Session() as sess:

    sess.run(tf.global_variables_initializer())

#     x_valid = np.load('valid_X.npy')
#     x_valid = np.reshape(x_valid, [5000, 64,64,1])
    x_test = np.load('test_X.npy')
    # split the test images vertically into 2 arrays of 5000x4096 because 10k is too much to do at once
    # tested it by concatenating two valid_X sets together, hopefully no problems with the test set
    list1, list2 = np.vsplit(x_test, 2)
    x_test = np.reshape(list1, [5000, 64, 64, 1])
#     y_valid = np.load('valid_Y.npy')
#     y_test = np.load('test_Y.npy')
    
    saver = tf.train.Saver()
    # load the model 
    saver.restore(sess, "./cls_model.dat")  

    predictions = sess.run(cls_logits, {x: x_test, train: False})
    predictions = np.reshape(predictions,[5000, 2, 10])
    
    # test against the first part of the test set
    cls_predictions1 = np.zeros((5000, 2), int)
    # gather predictions from test set now
    count = 0
    for row in predictions:
      pred = []
      for prediction in row:
        label = np.argmax(prediction)
        pred.append(label)

      # ascending order always  
      pred.sort()
      
      cls_predictions1[count][0] = int(pred[0])
      cls_predictions1[count][1] = int(pred[1])
      count += 1    
    
    # take care of the second half of the test set
    x_test = np.reshape(list2, [5000, 64, 64, 1])
    predictions = sess.run(cls_logits, {x: x_test, train: False})
    predictions = np.reshape(predictions,[5000, 2, 10])
    cls_predictions2 = np.zeros((5000, 2), int) 
    
    # oom error thrown when trying to add 10k to a single prediction list
    count = 0
    for row in predictions:
      pred = []
      for prediction in row:
        label = np.argmax(prediction)
        pred.append(label)

      pred.sort()  
      cls_predictions2[count][0] = int(pred[0])
      cls_predictions2[count][1] = int(pred[1])
      count += 1   
    
    # concatenate the classification predictions
    cls_predictions = np.concatenate([cls_predictions1, cls_predictions2])
    
  return cls_predictions

    
def bb_test():
  
  tf.reset_default_graph()
  
  x = tf.placeholder(tf.float32, (None, 64, 64, 1))
  y = tf.placeholder(tf.float32, (None, 8)) 
  train = tf.placeholder(tf.bool)
  bb_logits = bb_net(x, train)  
  
  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
  
#     x_valid = np.load('valid_X.npy')
#     x_valid = np.reshape(x_valid, [5000, 64,64,1])
    x_test = np.load('test_X.npy')
    # split vertically
    list1, list2 = np.vsplit(x_test, 2)
    x_test = np.reshape(list1, [5000, 64, 64, 1])    
#     y_test = np.load('test_Y.npy')
#     bb_valid = np.load('valid_bboxes.npy')
#     bb_test = np.load('test_bboxes.npy')
    
    saver = tf.train.Saver()
    saver.restore(sess, './bb_model.dat')
    
    #change these back to x_test after done messing around with valid set
    predictions = sess.run(bb_logits, {x: x_test, train: False})
    bb_predictions1 = np.reshape(predictions,[5000, 2, 4])
    
    # second part of the test set
    x_test = np.reshape(list2, [5000, 64, 64, 1])  
    predictions = sess.run(bb_logits, {x: x_test, train: False})
    bb_predictions2 = np.reshape(predictions,[5000, 2, 4])

    # concatenate the prediction lists after I am done
    bb_predictions = np.concatenate([bb_predictions1, bb_predictions2])
    
  return bb_predictions

if __name__ == '__main__':
    # set TRAIN to True if you want to train
    TRAIN = False
    if TRAIN:
        cls_train()
        bb_train()
    cls_results, bb_results = cls_test(), bb_test()
#     evaluation(cls_results, bb_results)
    evaluation_test(cls_results, bb_results)