# coding=utf-8
import tensorflow as tf
from tensorflow.python.ops import array_ops
import numpy as np
import cPickle


class BasicLSTM(object):
    def __init__(self, hidden_size, input_size, output_size, num_steps, learning_rate):
        self.hidden_size = hidden_size
        self.input_size = input_size
        self.output_size = output_size
        self.num_steps = num_steps
        self.learning_rate = learning_rate
        with tf.variable_scope(type(self).__name__, reuse=False):
            # TODO: use tensor array
            var_names = ['Wf', 'bf', 'Wi', 'bi', 'Wo', 'bo', 'Wc', 'bc']
            for var in var_names:
                if var.startswith('W'):
                    tf.get_variable(var, shape=(self.hidden_size, self.hidden_size + self.input_size),
                                    dtype=np.float32, initializer=tf.uniform_unit_scaling_initializer())
                elif var.startswith('b'):
                    tf.get_variable(var, shape=self.hidden_size,
                                        dtype=np.float32, initializer=tf.constant_initializer(0.0))
                else:
                    raise Exception(var)
            # output matrix
            tf.get_variable("Wout", shape=(self.output_size, self.hidden_size),
                            dtype=np.float32, initializer=tf.uniform_unit_scaling_initializer())
            tf.get_variable("bout", shape=self.output_size, dtype=np.float32,
                            initializer=tf.constant_initializer(0.0))
        self.var_names = var_names + ['Wout', 'bout']
        inputs = tf.placeholder(dtype=tf.float32, shape=[self.num_steps, self.input_size])
        targets = tf.placeholder(dtype=tf.float32, shape=[self.num_steps, self.input_size])
        target_weights = tf.placeholder(dtype=tf.float32, shape=[self.num_steps])
        h = tf.constant(np.zeros(self.hidden_size), dtype=tf.float32)
        c = tf.constant(np.zeros(self.hidden_size), dtype=tf.float32)
        loss = 0
        for t in range(0, num_steps):
            # TODO: use miniBatch
            with tf.variable_scope(type(self).__name__, reuse=True):
                var_list = []
                for var in self.var_names:
                    var_list.append(tf.get_variable(var))
                Wf, bf, Wi, bi, Wo, bo, Wc, bc, Wout, bout = var_list
            x = inputs[t, :]
            y = targets[t, :]
            y_weights = target_weights[t]
            h_x = tf.reshape(array_ops.concat(0, (h, x)), [-1, 1])
            # forget gate
            f = tf.sigmoid(tf.reshape(tf.matmul(Wf, h_x), [-1]) + bf)
            # input gate
            i = tf.sigmoid(tf.reshape(tf.matmul(Wi, h_x), [-1]) + bi)
            # output gate
            o = tf.sigmoid(tf.reshape(tf.matmul(Wo, h_x), [-1]) + bo)
            # new state candidates
            cand_c = tf.tanh(tf.reshape(tf.matmul(Wc, h_x), [-1]) + bc)
            # new state
            c = f * c + i * cand_c
            # new hidden state
            h = o * tf.tanh(c)
            lin_output = tf.reshape(tf.matmul(Wout, tf.reshape(h, [-1, 1])), [-1]) + bout
            output = tf.reshape(tf.nn.softmax(tf.reshape(lin_output, [1, -1])), [-1])
            loss += -tf.reduce_sum(tf.log(output) * y) * y_weights
        loss /= tf.reduce_sum(target_weights)
        train_step = tf.train.AdamOptimizer(self.learning_rate).minimize(loss)

        self.inputs = inputs
        self.targets = targets
        self.target_weights = target_weights
        self.loss = loss
        self.train_step = train_step
        

if __name__ == '__main__':
    dataset = cPickle.load(open('MNIST_data/mnist_seq.pkl', 'rb'))
    dataset = dataset[::2]
    print '{n} samples in the original dataset'.format(n=len(dataset))
    dataset = [x for x, y in dataset]
    input_size = vocab_size = 102 # including eos and padding
    eos = 100
    padding = 101
    seq_size = 15
    dataset_ = []
    for x in dataset:
        len_x = len(x)
        if len_x >= seq_size or len_x <= 5:
            continue
        elif len_x == seq_size - 1:
            x_ = np.hstack((x, np.array([eos], dtype=x.dtype)))
        else:
            x_ = np.hstack((x, np.array([eos], dtype=x.dtype), padding * np.ones(seq_size - len_x - 1, dtype=x.dtype)))
        assert(len(x_) == seq_size)
        dataset_.append((x_, len_x + 1))        
    dataset = dataset_
    print '{n} samples in the dataset'.format(n=len(dataset))

    output_size = input_size = vocab_size
    hidden_size = 2 * input_size
    learning_rate = 1e-3
    num_epochs = 10
    num_steps = seq_size - 1
    
    dataset_ = []
    for x, len_x in dataset:
        X = np.zeros((len(x), input_size), np.float32)
        X[np.arange(0, X.shape[0]), x] = 1.0
        data = X[0:-1, :]
        target = X[1:, :]
        target_weight = np.zeros(num_steps, dtype=np.float32)
        target_weight[np.arange(len_x - 1)] = 1.0
        dataset_.append((data, target, target_weight))
    dataset = dataset_
    
    np.random.seed(0)
    dataset = [dataset[i] for i in np.random.permutation(len(dataset))]
    split_point = int(0.9 * len(dataset))
    train_set = dataset[0 : split_point]
    valid_set = dataset[split_point :]
    print '{nt} training samples, {nv} validation samples'.format(nt=len(train_set), nv=len(valid_set))
    
    print 'building tensor graph...'
    lstm = BasicLSTM(input_size=input_size, hidden_size=hidden_size, output_size=output_size,
                     num_steps=num_steps, learning_rate=learning_rate)
    print 'tensor graph built.'
    
    with tf.Session() as sess:
        sess.run(tf.initialize_all_variables())
        # training
        for epoch in range(num_epochs):
            # validate the model
            loss = 0
            for data, target,  target_weight in valid_set:
                loss += sess.run(lstm.loss, feed_dict={lstm.inputs: data, lstm.targets: target, lstm.target_weights: target_weight})
            loss /= len(valid_set)
            print '{ep} epoch, validation loss {l:.4f}'.format(ep=epoch, l=loss)
            # update the parameter
            for data, target,  target_weight in train_set:
                sess.run([lstm.train_step, lstm.loss], feed_dict={lstm.inputs: data, lstm.targets: target, lstm.target_weights: target_weight})
            # dump the learnt parameters at the end of each epoch
            var_list = []
            for var in lstm.var_names:
                with tf.variable_scope(type(lstm).__name__, reuse=True):
                    var_list.append(sess.run(tf.get_variable(var)))
            cPickle.dump((var_list, loss), open("model/lstm_epoch{ep}.pkl".format(ep=epoch+1), "wb"))
