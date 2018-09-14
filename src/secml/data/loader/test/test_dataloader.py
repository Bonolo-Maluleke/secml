import unittest
from secml.utils import CUnitTest

from secml.data.loader import CDataLoader


class TestCDataLoader(CUnitTest):
    """Unit test for CDataLoaders."""

    def test_dl_instance(self):
        """Testing if all available loaders can be correctly initialized."""

        available_dataset = ['random', 'random_regression',
                             'random_blobs', 'random_blobs_regression',
                             'random_circles', 'random_circles_regression',
                             'random_moons', 'random_binary']

        for dl_str in available_dataset:
            self.logger.info("Loading dataset of type {:}...".format(dl_str))
            loader = CDataLoader.create(dl_str, n_samples=54)
            dataset = loader.load()
            self.assertEqual(54, dataset.num_samples)

    def test_binary_data_creation(self):
        """Tests on binary data creation."""
        shapes = [(100, 2), (200, 6), (1000, 100)]
        for samples, features in shapes:
            dataset = CDataLoader.create('random_binary', n_samples=samples, n_features=features).load()
            self.assertEquals(
                dataset.X.shape, (samples, features), "Wrong default shape for binary dataset")
            self.assertEquals(
                dataset.X[dataset.X > 1].shape[0], 0, "Data is not binary!")
            self.assertEquals(
                dataset.X[dataset.X < 0].shape[0], 0, "Data is not binary!")

if __name__ == '__main__':
    unittest.main()
