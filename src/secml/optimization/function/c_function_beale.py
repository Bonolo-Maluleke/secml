"""
.. module:: BealeFunction
   :synopsis: Beale function

.. moduleauthor:: Marco Melis <marco.melis@diee.unica.it>

"""
from c_function import CFunction
from secml.array import CArray


class CFunctionBeale(CFunction):
    """The Beale function.

    2-Dimensional, multimodal, with sharp peaks
    at the corners of the input domain.

    Global minimum f(x) = 0 @ x = (3, 0.5).

    Given by:
    .. math::

        f(x) = (1.5 - x_0 + x_0 * x_1)^2 + (2.25 - x_0 + x_0 * x_1^2)^2 +
         (2.625 - x_0 + x_0 * x_1^3)^2


    """
    class_type = 'beale'

    def __init__(self):

        # Passing data to CFunction
        super(CFunctionBeale, self).__init__(
            fun=self._fun, n_dim=2, gradient=self._grad)

    def _fun(self, x):
        """Apply Beale function to point x.

        Parameters
        ----------
        x : CArray
            Data point.

        """
        x = x.atleast_2d()
        if x.shape[1] != 2:
            raise ValueError(
                "Beale function available for 2 dimensions only")

        # Split into 3 parts
        f1 = (1.5 - x[0] + x[0] * x[1]) ** 2
        f2 = (2.25 - x[0] + x[0] * x[1] ** 2) ** 2
        f3 = (2.625 - x[0] + x[0] * x[1] ** 3) ** 2

        return f1 + f2 + f3

    def _grad(self, x):
        """Beale function gradient wrt. point x."""
        x = x.atleast_2d()
        if x.shape[1] != 2:
            raise ValueError("Gradient of Beale function "
                             "only available for 2 dimensions")
        # Computing gradient of each dimension
        grad1_1 = 2 * (1.5 - x[0] + x[0] * x[1]) * (-1 + x[1])
        grad1_2 = 2 * (2.25 - x[0] + x[0] * x[1] ** 2) * (-1 + x[1] ** 2)
        grad1_3 = 2 * (2.625 - x[0] + x[0] * x[1] ** 3) * (-1 + x[1] ** 3)
        grad2_1 = 2 * (1.5 - x[0] + x[0] * x[1]) * x[0]
        grad2_2 = 2 * (2.25 - x[0] + x[0] * x[1] ** 2) * (2 * x[0] * x[1])
        grad2_3 = 2 * (2.625 - x[0] + x[0] * x[1] ** 3) * \
            (3 * x[0] * x[1] ** 2)

        grad1 = CArray(grad1_1 + grad1_2 + grad1_3)
        grad2 = CArray(grad2_1 + grad2_2 + grad2_3)

        return CArray.concatenate(grad1, grad2, axis=1)
