"""
.. module:: CClassifierGradientTest
   :synopsis: Debugging class for the classifier gradient class

.. moduleauthor:: Ambra Demontis <ambra.demontis@diee.unica.it>

"""
from abc import ABCMeta, abstractmethod, abstractproperty

from secml.core import CCreator


class CClassifierGradientTest(CCreator):
    """
    This class implement different functionalities which are useful to test
    the CClassifierGradient class.
    """
    __metaclass__ = ABCMeta
    __super__ = 'CClassifierGradientTest'

    def __init__(self, gradients):
        self.gradients = gradients

    @abstractproperty
    def _params(self):
        """
        Classifier parameters
        """
        raise NotImplementedError()

    @abstractmethod
    def _L_tot(self, x, y, clf):
        """
        Classifier total loss
        L_tot = loss computed on the training samples + regularizer
        """
        raise NotImplementedError()

    @abstractmethod
    def _change_params(self, params, clf):
        """
        Return a deepcopy of the given classifier with the value of the
        parameters changed
        vector
        """
        raise NotImplementedError()

