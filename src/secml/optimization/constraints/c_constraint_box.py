'''
C_constraint
@author: Battista Biggio

This module contains the class for the Box constraint

'''

from secml.optimization.constraints import CConstraint
from secml.array import CArray
from secml.core.type_utils import is_scalar
from secml.core.constants import inf


class CConstraintBox(CConstraint):
    """Class that defines a box constraint."""
    class_type = "box"

    def __init__(self, lb=None, ub=None):
        self.lb = lb
        self.ub = ub

    @property
    def lb(self):
        """Returns lower bound."""
        return self._lb

    @lb.setter
    def lb(self, value):
        value = -inf if value is None else value
        self._lb = CArray(value).ravel()

    @property
    def ub(self):
        """Returns upper bound."""
        return self._ub

    @ub.setter
    def ub(self, value):
        """Sets upper bound."""
        value = inf if value is None else value
        self._ub = CArray(value).ravel()

    @property
    def center(self):
        return CArray(0.5 * (self.ub + self.lb)).ravel()

    @property
    def radius(self):
        return CArray(0.5 * (self.ub - self.lb)).ravel()

    def set_center_radius(self, c, r):
        """This function enables setting a box constraint in terms of
        its center and radius. c and r can be either scalars or CArray."""
        self.lb = c - r
        self.ub = c + r

    def set_lb_ub(self, lb, ub):
        """This function enables setting a box constraint in terms of
        lb and ub. lb and ub can be either scalars or CArray."""
        self.lb = lb
        self.ub = ub

    def _constraint(self, x):
        """Returns an integer that depends on
        the position of the point inside the box."""

        # if x is sparse, and center and radius are not (sparse) vectors,
        # call sparse implementation
        if x.issparse and self.center.size != x.size and \
                self.radius.size != x.size:
            return self._constraint_sparse(x)

        z = abs(x - self.center) - self.radius
        return z.max()

    def _constraint_sparse(self, x):
        """Returns an integer that depends on
        the position of the point inside the box."""

        if self.center.size > 1 and self.radius.size > 1:
            raise ValueError("Box center and radius are not scalar values.")

        m0 = abs(0 - self.center) - self.radius
        if x.nnz == 0:
            return m0

        # computes constraint values (l-inf dist. to center) for nonzero values
        z = abs(CArray(x.nnz_data).todense() - self.center) - self.radius
        m = z.max()
        # if there are no zeros in x... (it may be effectively "dense")
        if x.nnz == x.size:
            # return current maximum value
            return m

        # otherwise evaluate also the l-inf dist. of 0 elements to the center,
        # and also consider that in the max computation
        return max(m, m0)

    def _projection(self, x):
        """Project x onto the feasible domain (box)."""

        if is_scalar(self._ub):
            x[x >= self._ub] = self._ub
        else:
            x[x >= self._ub] = self._ub[x >= self._ub]

        if is_scalar(self._lb):
            x[x <= self._lb] = self._lb
        else:
            x[x <= self._lb] = self._lb[x <= self._lb]

        return x
