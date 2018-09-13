"""
.. module:: RegularizerL2
   :synopsis: L2-Norm Regularizer Function

.. moduleauthor:: Marco Melis <marco.melis@diee.unica.it>
.. moduleauthor:: Ambra Demontis <ambra.demontis@diee.unica.it>

"""
from prlib.classifiers.regularizer import CRegularizer
from prlib.array import CArray


class CRegularizerL2(CRegularizer):
    """Norm-L2 Regularizer.

    L2 Regularizer is given by:

    ..math:

        R(w) := \frac{1}{2} \sum_{i=1}^{n} w_i^2

    """

    class_type = 'l2'

    def regularizer(self, w):
        """Returns Norm-L2.

        Parameters
        ----------
        w : CArray
            Vector-like array.

        """
        return 0.5 * (w ** 2).sum()

    def dregularizer(self, w):
        """Return Norm-L2 derivative.

        Parameters
        ----------
        w : CArray
            Vector-like array.

        """
        return w
