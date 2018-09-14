import unittest
import numpy as np

import pylab as pl
from matplotlib.colors import ListedColormap

from secml.utils import CUnitTest
from secml.classifiers import CClassifierKNN
from secml.data import CDataset
from secml.data.loader import CDLRandom
from secml.peval.metrics import CMetricAccuracy


class TestCClassifierKNN(CUnitTest):
    """Unit test for CClassifierKNN."""

    def setUp(self):

        ds = CDLRandom(n_samples=100, n_features=2, n_redundant=0,
                       n_informative=1, n_clusters_per_class=1,
                       random_state=10000).load()
        self.logger.info("Initializing KNeighbors Classifier... ")
        self.dataset = ds[:50, :]
        self.test = ds[50:, :]
        self.KN_classifier = CClassifierKNN(n_neighbors=3)
        self.KN_classifier.train(self.dataset)

    def test_plot_dataset(self):
        self.logger.info("Draw the dataset... ")

        x_min = self.dataset.X[:, 0].min() - 1
        x_max = self.dataset.X[:, 0].max() + 1
        y_min = self.dataset.X[:, 1].min() - 1
        y_max = self.dataset.X[:, 1].max() + 1
        self.step = 0.08
        xx, yy = np.meshgrid(np.arange(x_min, x_max, self.step),
                             np.arange(y_min, y_max, self.step))
        self.grid = CDataset(np.c_[xx.ravel(), yy.ravel()])
        lab, Z_tree = self.KN_classifier.classify(self.grid.X)
        Z_tree = Z_tree[:, 1]
        Z_tree = Z_tree.reshape(xx.shape)
        cmap_light = ListedColormap(['#FFAAAA', '#AAFFAA', '#AAAAFF'])
        cmap_bold = ListedColormap(['#FF0000', '#00FF00', '#0000FF'])
        # cs = pl.contourf(xx, yy, Z_tree.data, 50)
        # cs = pl.contour(cs, levels=[0],colors = 'k', hold='on')
        pl.pcolormesh(xx, yy, Z_tree.get_data(), cmap=cmap_light)

        pl.scatter(self.dataset.X.get_data()[:, 0],
                   self.dataset.X.get_data()[:, 1],
                   c=self.dataset.Y.get_data(), marker='o', cmap=cmap_bold)
        pl.show()

    def test_classification(self):
        self.logger.info("Check the classification method... ")

        lab_cl, score = self.KN_classifier.classify(self.test.X)

        acc = CMetricAccuracy().performance_score(self.test.Y, lab_cl)

        self.logger.info("Real label:\n{:}".format(self.test.Y.tolist()))
        self.logger.info("Predicted label:\n{:}".format(lab_cl.tolist()))

        self.logger.info("Accuracy: {:}".format(acc))

        self.assertGreater(acc, 0.9)

    def test_kneighbors(self):
        single_sample = self.test.X[0, :]
        array_samples = self.test.X[1:11, :]

        self.logger.info("Checking KNN classifier on a single sample...")
        num_samp = 3
        with self.timer():
            dist, index_n, corresp = self.KN_classifier.kneighbors(
                single_sample, num_samp)
        self.logger.info("Sample to evaluate: {:}".format(single_sample))
        self.logger.info("")
        self.logger.info("Closest: {:}, index {:}, distance {:}"
                         "".format(corresp[dist.argmin(), :],
                                   index_n[dist.argmin()],
                                   dist.min()))

        self.logger.info("Checking KNN classifier on multiple samples...")
        num_samp = 2
        with self.timer():
            dist, index_n, corresp = self.KN_classifier.kneighbors(
                array_samples, num_samp)
        for i in xrange(0, 10):
            self.logger.info("Sample to evaluate: {:}".format(single_sample))
            self.logger.info("Closest: {:}, index {:}, distance {:}"
                             "".format(corresp[i, :], index_n[i], dist[i, :]))


if __name__ == '__main__':
    unittest.main()
