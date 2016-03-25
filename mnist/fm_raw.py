#coding=utf-8
import numpy as np
import tensorflow as tf
import cPickle
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import array_ops
from tensorflow.examples.tutorials.mnist import input_data

def calc_XXT(X):
    return np.apply_along_axis(lambda x: np.outer(x, x).reshape((-1)), 1, X)

if __name__ == '__main__':
    mnist = input_data.read_data_sets("MNIST_data/", one_hot=False)
    m = (mnist.train.labels == 2) | ((mnist.train.labels == 5))
    train_images = mnist.train.images[m]
    train_labels = np.float32(mnist.train.labels[m])
    train_labels[train_labels == 2] = -1
    train_labels[train_labels == 5] = 1
    print 'training set: {p} positives, {n} negatives'.format(p=(train_labels==1).sum(), n=(train_labels==-1).sum())
    
    m = (mnist.validation.labels == 2) | ((mnist.validation.labels == 5))
    validation_images = mnist.validation.images[m]
    validation_labels = np.float32(mnist.validation.labels[m])
    validation_labels[validation_labels == 2] = -1
    validation_labels[validation_labels == 5] = 1
    print 'validation set: {p} positives, {n} negatives'.format(p=(validation_labels==1).sum(), n=(validation_labels==-1).sum())
    
    m = (mnist.test.labels == 2) | ((mnist.test.labels == 5))
    test_images = mnist.test.images[m]
    test_labels = np.float32(mnist.test.labels[m])
    test_labels[test_labels == 2] = -1
    test_labels[test_labels == 5] = 1
    print 'test set: {p} positives, {n} negatives'.format(p=(test_labels==1).sum(), n=(test_labels==-1).sum())
    
    input_dim = train_images.shape[1]
    num_train_samples = train_images.shape[0]
    
    latent_dim = 10
    learning_rate = 1e-2
    penalty_V = 1e-2
    penalty_w = 1e-2
    batch_size = 50
    num_epochs = 500
    probe_epochs = 5
    #validation_epochs = int(0.2 * num_train_samples / batch_size)
    #improve_margin = 0.1
    #patience_epochs = int(0.5 * num_train_samples / batch_size)
    #early_stop_epochs = 3 * validation_epochs
    
    # build graph
    X = tf.placeholder(tf.float32, (None, input_dim))
    XXT = tf.placeholder(tf.float32, (None, input_dim * input_dim))
    y_ = tf.placeholder(tf.float32, (None,))
    learning_rate_tsr = tf.placeholder(tf.float32)
    w0 = tf.Variable(0.0)
    w = tf.Variable(tf.truncated_normal([input_dim, 1], stddev=1.0/np.sqrt(input_dim), seed=0))
    V = tf.Variable(tf.truncated_normal([input_dim, latent_dim], stddev=1.0/np.sqrt(input_dim), seed=1))
    VVT = tf.matmul(V, V, transpose_a=False, transpose_b=True)
    y = w0 + tf.matmul(X, w) + tf.matmul(XXT, tf.reshape(VVT, [-1, 1]))
    y = tf.reshape(y, [-1])
    nll = -tf.reduce_mean(tf.log(tf.nn.sigmoid(y * y_)))
    reg_V = tf.reduce_sum(V * V)
    reg_w = tf.reduce_sum(w * w)
    loss = nll + penalty_w * reg_w + penalty_V * reg_V
    train_step = tf.train.AdamOptimizer(learning_rate_tsr).minimize(loss)
    is_correct = tf.greater(y * y_, 0)
    accuracy = tf.reduce_mean(tf.cast(is_correct, tf.float32))
    
    ## train model, using tricky gradient descent
    #sess = tf.Session()
    #sess.run(tf.initialize_all_variables())
    #print '|V|.sum is {s}'.format(s=np.abs(sess.run(V)).sum())
    #num_samples = train_images.shape[0]
    #last_validation_loss = None
    #validation_counter = 0
    #termination_epoch_counter = 0
    #head = 0
    #indices = range(num_samples)
    #for i in range(num_epochs):
    #    if head + batch_size > num_samples:
    #        indices = np.random.permutation(num_samples)
    #        head = 0
    #    selected = indices[head: head + batch_size]
    #    head += batch_size
    #    batch_x = train_images[selected]
    #    batch_y = train_labels[selected]
    #    batch_xxt = calc_XXT(batch_x)
    #    validation_counter += 1
    #    if last_validation_loss is not None:
    #        if validation_counter % validation_epochs == 0:
    #            validation_loss = 0.0
    #            num_validation_samples = validation_images.shape[0]
    #            validation_num_batches = int(num_validation_samples/batch_size)
    #            for k in range(0, validation_num_batches):
    #                batch_x = validation_images[k*batch_size : (k+1)*batch_size]
    #                batch_xxt = calc_XXT(batch_x)
    #                batch_y = validation_labels[k*batch_size : (k+1)*batch_size]
    #                loss = sess.run(nll, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
    #                validation_loss += loss
    #            validation_loss /= validation_num_batches
    #            if validation_loss <= last_validation_loss * (1 - improve_margin):
    #                termination_epoch_counter = 0
    #            else:
    #                learning_rate /= 2.0
    #                termination_epoch_counter += validation_epochs
    #            print '{i}, last_validation_loss {ll}, validation_loss {l}, learning rate {r}, improve_margin {m}, termination_epoch_counter {t}'.format(i=i, ll=last_validation_loss, l=validation_loss, r=learning_rate, m=improve_margin, t=termination_epoch_counter)
    #            last_validation_loss = validation_loss
    #    if termination_epoch_counter >= early_stop_epochs:
    #        print 'termination criterion satisfied at step {i}'.format(i=i)
    #        break
    #    if i == patience_epochs:
    #        validation_loss = 0.0
    #        num_validation_samples = validation_images.shape[0]
    #        validation_num_batches = int(num_validation_samples/batch_size)
    #        print '{i}, num_validation_samples {n}'.format(i=i, n=num_validation_samples)
    #        print '{i}, validation_num_batches {n}'.format(i=i, n=validation_num_batches)
    #        for k in range(0, validation_num_batches):
    #            #print '[{a}, {b})'.format(a=k*batch_size, b=(k+1)*batch_size)
    #            batch_x = validation_images[k*batch_size : (k+1)*batch_size]
    #            batch_xxt = calc_XXT(batch_x)
    #            batch_y = validation_labels[k*batch_size : (k+1)*batch_size]
    #            loss = sess.run(nll, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
    #            validation_loss += loss
    #        validation_loss /= validation_num_batches
    #        print '{i}, validation_loss {l}'.format(i=i, l=validation_loss)
    #        last_validation_loss = validation_loss
    #        validation_counter = 0
    #    if i % probe_epochs == 0:
    #        nll_this_step = sess.run(nll, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
    #        reg_V_this_step = sess.run(reg_V)
    #        reg_w_this_step = sess.run(reg_w)
    #        accuracy_this_step = sess.run(accuracy, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
    #        print 'step {i}, accuracy {a:.2f}%, reg_V {v:.3f}, reg_w {w:.3f}, nll {n:.3f}'\
    #            .format(i=i, a=accuracy_this_step*100.0, v=reg_V_this_step, w=reg_w_this_step, n=nll_this_step)
    #    sess.run(train_step, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y, learning_rate_tsr: learning_rate})

    # train model, using naive gradient descent
    sess = tf.Session()
    sess.run(tf.initialize_all_variables())
    print '|V|.sum is {s}'.format(s=np.abs(sess.run(V)).sum())
    num_samples = train_images.shape[0]
    validation_loss_list = []
    head = 0
    indices = range(num_samples)
    for i in range(num_epochs):
        if head + batch_size > num_samples:
            indices = np.random.permutation(num_samples)
            head = 0
        selected = indices[head: head + batch_size]
        head += batch_size
        batch_x = train_images[selected]
        batch_y = train_labels[selected]
        batch_xxt = calc_XXT(batch_x)
        if i % probe_epochs == 0:
            nll_this_step = sess.run(nll, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
            reg_V_this_step = sess.run(reg_V)
            reg_w_this_step = sess.run(reg_w)
            accuracy_this_step = sess.run(accuracy, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
            print 'step {i}, accuracy {a:.2f}%, reg_V {v:.3f}, reg_w {w:.3f}, nll {n:.3f}'\
                .format(i=i, a=accuracy_this_step*100.0, v=reg_V_this_step, w=reg_w_this_step, n=nll_this_step)
            # vdalition set
            validation_loss = 0.0
            num_validation_samples = validation_images.shape[0]
            validation_num_batches = int(num_validation_samples/batch_size)
            for k in range(validation_num_batches):
                batch_x = validation_images[k*batch_size : (k+1)*batch_size]
                batch_xxt = calc_XXT(batch_x)
                batch_y = validation_labels[k*batch_size : (k+1)*batch_size]
                loss = sess.run(nll, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y})
                validation_loss += loss
            validation_loss /= validation_num_batches
            validation_loss_list.append((i*batch_size, validation_loss))
            print 'step {i}, validation_loss {l:.4f}'.format(i=i, l=validation_loss)
        sess.run(train_step, feed_dict={X: batch_x, XXT: batch_xxt, y_: batch_y, learning_rate_tsr: learning_rate})

    with open('validation_loss.pkl', 'wb') as f:
        cPickle.dump(validation_loss_list, f)
    # test model
    predictions = None
    num_test_samples = test_images.shape[0]
    #TODO: run over the entire test set
    for i in range(0, int(num_test_samples/batch_size)):
        batch_x = test_images[i*batch_size : (i+1)*batch_size]
        batch_xxt = calc_XXT(batch_x)
        pred = sess.run(y, feed_dict={X: batch_x, XXT: batch_xxt})
        if predictions is None:
            predictions = pred
        else:
            predictions = np.concatenate((predictions, pred))
    n = predictions.shape[0]
    targets = test_labels[0:n]
    accuracy_test_set = (predictions * targets > 0).mean()
    print 'accuracy on test set is {a:.2f}%'.format(a=accuracy_test_set*100.0)
    #sess.close()