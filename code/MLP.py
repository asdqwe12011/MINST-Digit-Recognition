import numpy as np
import Activations as av


class MLPClassifier:
    def __init__(self, hidden_layer_sizes=(100,), activation='relu', solver='sgd', alpha=0.001,
                 batch_size=200, learning_rate_init=0.001, max_iter=200, shuffle=True, tol=1e-4,
                 n_iter_no_change=10):
        self.hidden_layers = len(hidden_layer_sizes)
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.slover = solver
        self.batch_size = batch_size
        self.learning_rate_init = learning_rate_init
        # L2 penalty
        self.alpha = alpha
        self.max_iter = max_iter
        self.shuffle = shuffle
        self.tol = tol
        self.n_iter_no_change = n_iter_no_change

    def fit(self, X_train, y_train):
        if X_train.ndim == 1:
            # reshape (N,) to (N, 1)
            X_train = X_train[:, None]

        (self.N, self.D), self.C = X_train.shape, np.max(y_train) + 1
        self.coefs_, self.intercepts_ = self._weight_init()

        # minibatch stoch gradient descent
        inds = np.random.permutation(self.N)
        t = 0
        for i in range(self.max_iter):
            if t > self.n_iter_no_change:
                return

            if self.shuffle:
                inds = np.random.permutation(self.N)

            batches_X = [X_train[inds[k:k + self.batch_size], :] for k in range(0, self.N, self.batch_size)]
            batches_y = [y_train[inds[k:k + self.batch_size]] for k in range(0, self.N, self.batch_size)]

            for batch_X, batch_y in zip(batches_X, batches_y):
                dws, dbs = self._backprop(batch_X, batch_y)
                # update Ws and bs
                self.coefs_ = [w - (self.learning_rate_init / self.batch_size) * dw for w, dw in zip(self.coefs_, dws)]
                self.intercepts_ = [b - (self.learning_rate_init / self.batch_size) * db for b, db in
                                    zip(self.intercepts_, dbs)]
        return

    def predict_proba(self, X):
        as_, _ = self._forward_pass(X)
        return as_[-1].transpose()

    def predict(self, X):
        prob = self.predict_proba(X)
        yh = np.argmax(prob, axis=-1)
        return yh

    def score(self, X_test, y_test):
        return np.sum(self.predict(X_test) == y_test) / y_test.shape[0]

    def _forward_pass(self, X):
        # activation function
        g = av.ACTIVATION(self.activation)
        g_out = av.ACTIVATION('softmax')

        # combine bias
        if X.ndim == 1:
            X = X[None, :]
        X = X.transpose()

        # after being activated and before being activated
        as_ = [X]  # from input layer to output layer
        zs = []  # from first hidden layer to output layer

        cur_layer = X
        for w, b in zip(self.coefs_[:-1], self.intercepts_[:-1]):
            z = np.matmul(w, cur_layer) + b
            cur_layer = g(z)
            as_.append(cur_layer)
            zs.append(z)

        # output layer
        w = self.coefs_[-1]
        b = self.intercepts_[-1]
        as_.append(g_out(np.matmul(w, cur_layer) + b))
        return as_, zs

    def _backprop(self, X, y):

        dg = av.D_ACTIVATION(self.activation)
        dw = [np.zeros(w.shape) for w in self.coefs_]
        db = [np.zeros(b.shape) for b in self.intercepts_]
        n = X.shape[0]

        as_, zs = self._forward_pass(X)
        y = self._OneHot_Encoding(y)
        # Compute the output layer
        theta = (as_[-1] - y)
        dw[-1] = np.matmul(theta, as_[-2].transpose())
        db[-1] = np.sum(theta, axis=-1)[:, None]

        # Compute the Hidden Layers
        for i in range(self.hidden_layers - 1, -1, -1):
            theta = np.matmul(self.coefs_[i + 1].transpose(), theta) * dg(zs[i])
            dw[i] = (1 + self.alpha / n) * np.matmul(theta, as_[i].transpose())
            db[i] = np.sum(theta, axis=-1)[:, None]

        return dw, db

    def _weight_init(self):
        # from input layer to output layer sizes
        layers_size = list(self.hidden_layer_sizes)
        layers_size.append(self.C)
        layers_size.insert(0, self.D)

        # initialize weight matrics and weight biases
        coefs_ = []
        intercepts_ = []
        for j in range(len(layers_size) - 1):
            ncur = layers_size[j]
            nnext = layers_size[j + 1]

            if self.activation != 'relu':
                eps = 4. * np.sqrt(6) / np.sqrt(ncur + nnext)
                # normalization to +-epsilon according to paper1
                w = eps * ((np.random.rand(nnext, ncur) * 2.) - 1)
                b = eps * ((np.random.rand(nnext, 1) * 2.) - 1)

            else:

                w = np.random.default_rng().normal(0., np.sqrt(2. / ncur), size=(nnext, ncur))
                b = np.random.default_rng().normal(0., np.sqrt(2. / ncur), size=(nnext, 1))

            coefs_.append(w)
            intercepts_.append(b)

        return coefs_, intercepts_

    def _OneHot_Encoding(self, y):
        # output shape (C, N)
        res = np.zeros((self.C, y.shape[-1]))
        for i in range(y.shape[-1]):
            res[y[i], i] = 1
        return res
