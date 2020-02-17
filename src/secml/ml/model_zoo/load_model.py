"""
.. module:: LoadModel
   :synopsis: Functions to load pre-trained SecML models

.. moduleauthor:: Marco Melis <marco.melis@unica.it>

"""
import json
import re

import secml
from secml.utils import fm
from secml.utils.download_utils import dl_file_gitlab

from secml.settings import SECML_MODELS_DIR

MODEL_ZOO_REPO_URL = 'https://gitlab.com/secml/secml-zoo'
MODELS_DICT_FILE = 'models_dict.json'
MODELS_DICT_PATH = fm.join(SECML_MODELS_DIR, MODELS_DICT_FILE)


def _dl_data_versioned(file_path, output_dir, md5_digest=None):
    """Download the from different branches depending on version.

    This function tries to download a model zoo resource from:
     1. the branch corresponding to current version,
        e.g. branch `v0.12` for `0.12.*` version
     2. the `master` branch

    Parameters
    ----------
    file_path : str
        Path to the file to download, relative to the repository.
    output_dir : str
        Path to the directory where the file should be stored.
        If folder does not exists, will be created.
    md5_digest : str or None, optional
        Expected MD5 digest of the downloaded file.
        If a different digest is computed, the downloaded file will be
        removed and ValueError is raised.

    """
    try:
        # Try downloading from the branch corresponding to current version
        min_version = re.search(r'^\d+.\d+', secml.__version__).group(0)
        dl_file_gitlab(MODEL_ZOO_REPO_URL, file_path, output_dir,
                       branch='v' + min_version, md5_digest=md5_digest)

    except RuntimeError:
        # Raised if file not found. Try looking in 'master' branch
        dl_file_gitlab(MODEL_ZOO_REPO_URL, file_path, output_dir,
                       branch='master', md5_digest=md5_digest)


def _get_models_dict():
    """Downloads the ditionary of models definitions.

    Returns
    -------
    models_dict : dict
        Dictionary with models definitions. Each key is an available model.
        Each model entry is defined by:
         - "model", path to the script with model definition
         - "state", path to the archive containing the pre-saved model state
         - "model_md5", md5 checksum of model definition
         - "state_md5", md5 checksum of pre-saved model state

    """
    # Download (if needed) data and extract it
    if not fm.file_exist(MODELS_DICT_PATH):

        # Download definitions from current version's branch first,
        # then from master branch
        _dl_data_versioned(MODELS_DICT_FILE, SECML_MODELS_DIR)

        # Check if file has been correctly downloaded
        if not fm.file_exist(MODELS_DICT_PATH):
            raise RuntimeError(
                'Something wrong happened while downloading the '
                'models definitions. Please try again.')

    with open(MODELS_DICT_PATH) as fp:
        return json.loads(fp.read())


MODELS_DICT = _get_models_dict()  # Populate the models dict


def load_model(model_id):
    """Load a pre-trained classifier.

    Returns a pre-trained SecML classifier given the id of the model.

    Check https://gitlab.com/secml/secml-zoo for the list of available models.

    Parameters
    ----------
    model_id : str
        Identifier of the pre-trained model to load.

    Returns
    -------
    CClassifier
        Desired pre-trained model.

    """
    model_info = MODELS_DICT[model_id]
    data_path = fm.join(SECML_MODELS_DIR, model_id, model_id + '.gz')
    # Download (if needed) data and extract it
    if not fm.file_exist(data_path):
        model_url = 'models/' + model_info['state'] + '.gz'
        out_dir = fm.join(SECML_MODELS_DIR, model_id)
        # Download requested model from current version's branch first,
        # then from master branch
        _dl_data_versioned(model_url, out_dir, model_info['state_md5'])

        # Check if file has been correctly downloaded
        if not fm.file_exist(data_path):
            raise RuntimeError('Something wrong happened while '
                               'downloading the model. Please try again.')

    def import_module(full_name, path):
        """Import a python module from a path."""
        from importlib import util

        spec = util.spec_from_file_location(full_name, path)
        mod = util.module_from_spec(spec)

        spec.loader.exec_module(mod)

        return mod

    # Name of the function returning the model
    model_name = model_info["model"].split('/')[-1]

    # Import the python module containing the function returning the model
    model_path = fm.join(
        fm.abspath(__file__), 'models', model_info["model"] + '.py')
    model_module = import_module(model_name, model_path)

    # Run the function returning the model
    model = getattr(model_module, model_name)()

    # Restore the state of the model from file
    model.load_state(data_path)

    return model
