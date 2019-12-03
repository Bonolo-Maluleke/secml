"""
.. module:: CClassifierDNN
   :synopsis: Base class for defining a DNN backend.

.. moduleauthor:: Maura Pintor <maura.pintor@unica.it>

"""
from abc import ABCMeta, abstractmethod
from functools import reduce

from secml.array import CArray
from secml.ml.classifiers import CClassifier


class CClassifierDNN(CClassifier, metaclass=ABCMeta):
    """CClassifierDNN, wrapper for DNN models.

    Parameters
    ----------
    model:
        backend-supported model
    preprocess:
        preprocessing module.
    softmax_outputs: bool, optional
        if set to True, a softmax function will be applied to
        the return value of the decision function. Note: some
        implementation adds the softmax function to the network
        class as last layer or last forward function, or even in the
        loss function (see torch.nn.CrossEntropyLoss). Be aware that the
        softmax may have already been applied.
        Default value is False.

    Attributes
    ----------
    class_type : 'dnn-clf'

    """
    __class_type = ' dnn-clf'

    def __init__(self, model, input_shape=None, preprocess=None,
                 pretrained=False, pretrained_classes=None,
                 softmax_outputs=False,
                 **kwargs):
        """
        Wrapper for DNN classifiers. All implemented DNN backends must
        inherit from this class and implement the abstract methods.

        Parameters
        ----------
        model: model dtype of the specific backend
            the model to wrap
        input_shape: tuple
            shape of the input for the DNN, it will
            be used for reshaping the input data to
            the expected shape
        preprocess: CPreprocess
            preprocessing module
        pretrained: bool, default False
            whether or not the model is pretrained. If the
            model is pretrained, the user won't need to call
            `fit` after loading the model.
        pretrained_classes: None or CArray, default None
            list of classes labels if the model is pretrained. If
            set to None, the class labels for the pretrained model should
            be inferred at the moment of initialization of the model
            and set to CArray.arange(n_classes)
        softmax_outputs: bool, default False
            whether or not to add a softmax layer after the
            logits.
        """
        super(CClassifierDNN, self).__init__(preprocess=preprocess)

        self._model = model
        self._out_layer = None
        self._trained = False

        self._model_layers = None
        self._model_layer_shapes = None
        self._pretrained = pretrained
        self._pretrained_classes = pretrained_classes
        self._input_shape = input_shape
        self._softmax_outputs = softmax_outputs
        self.check_softmax()

    @property
    def input_shape(self):
        """Returns the input shape of the first layer of the neural network."""
        return self._input_shape

    @input_shape.setter
    def input_shape(self, input_shape):
        self._input_shape = input_shape

    @property
    def softmax_outputs(self):
        return self._softmax_outputs

    @softmax_outputs.setter
    def softmax_outputs(self, active):
        """
        Defines whether to apply softmax to the final scores.

        Parameters
        ----------
        active : bool
            Activates the softmax in the output

        Notes
        ----------
        If the loss has softmax layer defined, or
        the network already has a softmax operation in the end
        this parameter will be disabled.
        """
        self._softmax_outputs = active
        self.check_softmax()

    @property
    @abstractmethod
    def layers(self):
        """Returns list of tuples containing the layers of the model.
        Each tuple is structured as (layer_name, layer)."""
        raise NotImplementedError

    @property
    def layer_names(self):
        """Returns the names of the layers of the model."""
        return list(zip(*(self.layers)))[0]

    @property
    @abstractmethod
    def layer_shapes(self):
        """Returns a dictionary containing the shapes of the output
        of each layer of the model."""
        raise NotImplementedError

    def check_softmax(self):
        """
        Checks if a softmax layer has been defined in the
        network.

        Returns
        -------
        Boolean value stating if a softmax layer has been
        defined.
        """
        if self._input_shape is not None:
            x = CArray.ones(reduce(lambda w, y: w * y, self.input_shape))
            outputs = self._forward(x)

            if outputs.sum() == 1:
                return True
            return False
        else:
            self.logger.info("Softmax cannot be checked if the input shape "
                             "is not passed as input. Disabling check.")

    @staticmethod
    @abstractmethod
    def _to_tensor(x):
        """Convert input CArray to backend-supported tensor."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _from_tensor(x):
        """Convert input backend-supported tensor to CArray"""
        raise NotImplementedError

    @abstractmethod
    def _forward(self, x):
        """Forward pass on input x.
        Returns the output of the layer set in _out_layer.
        If _out_layer is None, the last layer output is returned,
        after applying softmax if softmax_outputs is True.

        Parameters
        ----------
        x : CArray
            preprocessed array, ready to be transformed by the current module.

        Returns
        -------
        CArray
            Transformed input data.
        """
        raise NotImplementedError

    @abstractmethod
    def _backward(self, w):
        """Returns the gradient of the DNN - considering the output layer set
        in _out_layer - wrt data.

        Parameters
        ----------
        w : CArray
            Weights that are pre-multiplied to the gradient
            of the module, as in standard reverse-mode autodiff.

        Returns
        -------
        gradient : CArray
            Accumulated gradient of the module wrt input data.
        """
        raise NotImplementedError

    @abstractmethod
    def save_model(self, filename):
        """
        Stores the model and optimization parameters.

        Parameters
        ----------
        filename : str
            path of the file for storing the model

        """
        raise NotImplementedError

    @abstractmethod
    def load_model(self, filename):
        """
        Restores the model and optimization parameters.
        Notes: the model class should be
        defined before loading the params.

        Parameters
        ----------
        filename : str
            path where to find the stored model

        """
        raise NotImplementedError

    def get_layer_output(self, x, layer=None):
        """Returns the output of the desired net layer(s).

        Parameters
        ----------
        x : CArray
            Input data.
        layer : str or None, optional
            Name of the layer to get the output from.
            If None, the output of the last layer will be returned.

        Returns
        -------
        CArray
            Output of the desired layer.
        """
        self._out_layer = layer
        output = self.forward(x=x, caching=False)
        self._out_layer = None
        return output

    def get_layer_gradient(self, x, w, layer=None):
        """Computes the gradient of the classifier's decision function
         wrt input.

        Parameters
        ----------
        x : CArray
            Input sample
        w : CArray
            Will be passed to backward and must have a proper shape
            depending on the chosen output layer (the last one if `layer`
            is None). This is required if `layer` is not None.
        layer : str or None, optional
            Name of the layer.
            If None, the gradient at the last layer will be returned
            and `y` is required if `w` is None or softmax_outputs is True.
            If not None, `w` of proper shape is required.

        Returns
        -------
        gradient : CArray
            Gradient of the classifier's df wrt its input. Vector-like array.

        """
        self._out_layer = layer
        grad = self.gradient(x=x, w=w)
        self._out_layer = None
        return grad
