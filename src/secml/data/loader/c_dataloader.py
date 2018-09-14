"""
.. module:: DataLoader
   :synopsis: Load and save a dataset to/from disk

.. moduleauthor:: Marco Melis <marco.melis@diee.unica.it>
.. moduleauthor:: Davide Maiorca <davide.maiorca@diee.unica.it>
.. moduleauthor:: Ambra Demontis <ambra.demontis@diee.unica.it>

"""
from abc import ABCMeta, abstractmethod, abstractproperty
from secml.array import CArray
from secml.core import CCreator
from secml.data import CDataset


class CDataLoader(CCreator):
    """Interface for Dataset loaders."""
    __metaclass__ = ABCMeta
    __super__ = 'CDataLoader'

    @abstractproperty
    def class_type(self):
        """Type of the data loader (str). Will be used by `.create()`."""
        raise NotImplementedError

    @abstractmethod
    def load(self, *args, **kwargs):
        """Loads a dataset.

        This method should return a `.CDataset` object.

        """
        raise NotImplementedError("Please implement a `load` method for class {:}".format(self.__class__.__name__))

    # TODO: GENERALIZE THIS FUNCTION AND PUT IT INTO CARRAY
    @staticmethod
    def _remove_all_zero_features(patterns):
        """
        Return patterns with only non zero features

        Parameters
        ----------
        patterns : CArray
            Array with scattered data containing
            features which are all zero for each pattern

        Returns
        -------
        patterns : CArray
            Array with scattered data without features
            which are all zero for each pattern
        idx_mapping : CArray
            Mapping of features's indices to original data.

        Examples
        --------
        >>> from secml.data.loader import CDataLoader
        >>> patterns = CArray([[1,0,2], [4,0,5]])
        >>> patterns, mapping = CDataLoader._remove_all_zero_features(patterns)
        >>> print patterns
        CArray([[1 2]
         [4 5]])
        >>> print mapping
        CArray([0 2])

        """
        all_feat_num = patterns.shape[1]
        all_orig_feat_idx = CArray.arange(start=0, stop=all_feat_num)

        # found indices that are really features (not zero for every pattern)
        nnz_elem_idx = patterns.nnz_indices
        idx_feat_presents = CArray(nnz_elem_idx[1]).unique()

        # return dataset without features that are all zero and non zero old idx
        return patterns[:, idx_feat_presents], all_orig_feat_idx[idx_feat_presents]


