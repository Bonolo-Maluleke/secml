import unittest
from secml.utils import CUnitTest
from secml.array import CArray
from secml.data.loader import CDLRandom
from secml.classifiers import CClassifierSVM
from secml.peval.metrics import CRoc

from secml.figure import CFigure


class TestCRoc(CUnitTest):
    """Unit test for CRoc."""

    def setUp(self):

        self.dl1 = CDLRandom(n_features=1000, n_redundant=200,
                             n_informative=250, n_clusters_per_class=2,
                             random_state=0)
        self.dl2 = CDLRandom(n_features=1000, n_redundant=200,
                             n_informative=250, n_clusters_per_class=2,
                             random_state=1000)
        self.ds1 = self.dl1.load()
        self.ds2 = self.dl2.load()

        self.svm = CClassifierSVM(C=1e-7).train(self.ds1)

        self.y1, self.s1 = self.svm.classify(self.ds1.X)
        self.y2, self.s2 = self.svm.classify(self.ds2.X)

        self.roc = CRoc()

    def test_roc_1sample(self):

        self.roc.compute(CArray([1]), CArray([0]))
        self.roc.average()

        # Testing 3 and not 1 as roc is bounded (we add a first and last point)
        self.assertEqual(self.roc.fp.size, 3)
        self.assertEqual(self.roc.tp.size, 3)

    def test_compute(self):

        self.roc.compute(self.ds1.Y, self.s1[:, 1].ravel())

        fig = CFigure()
        fig.sp.semilogx(self.roc.fp, self.roc.tp)
        fig.sp.grid()
        fig.show()

    def test_mean(self):

        self.roc.compute([self.ds1.Y, self.ds2.Y],
                         [self.s1[:, 1].ravel(), self.s2[:, 1].ravel()])
        mean_fp, mean_tp, mean_std = self.roc.average(return_std=True)
        fig = CFigure(linewidth=2)
        fig.sp.errorbar(
            self.roc.mean_fp, self.roc.mean_tp, yerr=mean_std)
        for rep in xrange(self.roc.n_reps):
            fig.sp.semilogx(self.roc.fp[rep], self.roc.tp[rep])
        fig.sp.semilogx(mean_fp, mean_tp)
        fig.sp.grid()
        fig.show()


if __name__ == '__main__':
    unittest.main()
