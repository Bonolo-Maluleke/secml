"""
.. module:: ClassifierDecisionTree
   :synopsis: Decision Treee classifier

.. moduleauthor:: Paolo Russu <paolo.russu@diee.unica.it>
.. moduleauthor:: Marco Melis <marco.melis@diee.unica.it>

"""
import sklearn
from sklearn import tree

from prlib.array import CArray
from prlib.classifiers import CClassifier


class CClassifierDecisionTree(CClassifier):
    """Decision Tree Classifier"""
    class_type = 'tree'

    def __init__(self, criterion='gini', splitter='best',
                 max_depth=None, min_samples_split=2, normalizer=None):

        # Calling CClassifier constructor
        CClassifier.__init__(self, normalizer=normalizer)

        # Classifier Parameters
        self.criterion = criterion
        self.splitter = splitter
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split

        self._dt = None

    def __clear(self):
        """Reset the object."""
        self._dt = None

    def is_clear(self):
        """Returns True if object is clear."""
        return self._dt is None and \
            super(CClassifierDecisionTree, self).is_clear()

    @property
    def min_samples_split(self):
        """Return decision tree min_samples_split."""
        return self._min_samples_split

    @min_samples_split.setter
    def min_samples_split(self, value):
        """Return decision tree min_samples_split."""
        self._min_samples_split = int(value)

    def _train(self, dataset):
        """Trains the Decision Tree classifier."""
        if dataset.issparse is True and sklearn.__version__ < '0.16':
            raise ValueError(
                "sparse dataset is not supported if sklearn version < 0.16.")

        self._dt = tree.DecisionTreeClassifier(
            criterion=self.criterion,
            splitter=self.splitter,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split)

        self._dt.fit(dataset.X.get_data(), dataset.Y.tondarray())

        return self._dt

    def _discriminant_function(self, x, label=1):
        """Compute the discriminant function for pattern 'x'."""
        x_carray = CArray(x)
        if x_carray.issparse is True and sklearn.__version__ < '0.16':
            raise ValueError(
                "sparse input is not supported if sklearn version < 0.16.")

        return CArray(self._dt.predict_proba(x_carray.get_data())[:, label])
