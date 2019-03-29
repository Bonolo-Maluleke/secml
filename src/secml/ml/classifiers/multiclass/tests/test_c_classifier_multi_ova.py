from six.moves import range

from secml.ml.classifiers.tests import CClassifierTestCases

from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC

from secml.array import CArray
from secml.data.loader import CDLRandom
from secml.ml.classifiers import CClassifierSVM
from secml.ml.classifiers.multiclass import CClassifierMulticlassOVA
from secml.ml.peval.metrics import CMetric
from secml.figure import CFigure


class TestCClassifierMultiOVA(CClassifierTestCases):
    """Unittests for CClassifierMultiOVA."""

    def setUp(self):
        # generate synthetic data
        self.dataset = CDLRandom(n_classes=4, n_clusters_per_class=1).load()

    def test_predict_withsvm(self):

        svc = SVC(kernel='linear', class_weight='balanced')
        multiclass_sklearn = OneVsRestClassifier(svc)
        multiclass = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                              class_weight='balanced')
        multiclass.verbose = 2

        multiclass.fit(self.dataset, n_jobs=2)
        class_pred, score_pred = multiclass.predict(
            self.dataset.X, n_jobs=2, return_decision_function=True)

        self.logger.info("Predicted: \n{:}".format(class_pred))
        self.logger.info("Real: \n{:}".format(self.dataset.Y))

        acc = CMetric.create('accuracy').performance_score(
            self.dataset.Y, class_pred)
        self.logger.info("Accuracy: {:}".format(acc))

        multiclass_sklearn.fit(self.dataset.X.get_data(),
                               self.dataset.Y.tondarray())
        y_sklearn = multiclass_sklearn.predict(self.dataset.X.get_data())

        acc_sklearn = CMetric.create('accuracy').performance_score(
            self.dataset.Y, CArray(y_sklearn))
        self.logger.info("Accuracy Sklearn: {:}".format(acc_sklearn))

        self.assertLess(abs(acc - acc_sklearn), 0.01)

    def test_set(self):

        from secml.ml.kernel import CKernelRBF
        multiclass = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                              C=1, kernel=CKernelRBF())
        # Test set before training
        multiclass.set_params({'C': 100, 'kernel.gamma': 20})
        for clf in multiclass._binary_classifiers:
            self.assertEqual(clf.C, 100.0)
            self.assertEqual(clf.kernel.gamma, 20.0)

        # Restoring kernel
        multiclass.set('kernel', CKernelRBF(gamma=50))

        # Setting different parameter in single trained_classifiers
        multiclass.prepare(num_classes=4)
        different_c = (10, 20, 30, 40)
        multiclass.set('C', different_c)
        different_gamma = (50, 60, 70, 80)
        multiclass.set('kernel.gamma', different_gamma)

        # Fit multiclass classifier than test set after training
        multiclass.fit(self.dataset)

        for clf_idx, clf in enumerate(multiclass._binary_classifiers):
            self.assertEqual(clf.C, different_c[clf_idx])
            self.assertEqual(clf.kernel.gamma, different_gamma[clf_idx])

        # Test set after training
        multiclass.set_params({'C': 30, 'kernel.gamma': 200})
        for clf in multiclass._binary_classifiers:
            self.assertEqual(clf.C, 30.0)
            self.assertEqual(clf.kernel.gamma, 200.0)

        for clf in multiclass._binary_classifiers:
            self.assertEqual(clf.C, 30.0)
            self.assertEqual(clf.kernel.gamma, 200.0)

        # Setting parameter in single trained_classifiers
        multiclass._binary_classifiers[0].kernel.gamma = 300
        for i in range(1, multiclass.num_classifiers):
            self.assertNotEqual(
                multiclass._binary_classifiers[i].kernel.gamma, 300.0)

        # Setting different parameter in single trained_classifiers
        different_c = (100, 200, 300)

        # ValueError is raised as not enough binary classifiers are available
        with self.assertRaises(ValueError):
            multiclass.set('C', different_c)

        multiclass.prepare(num_classes=3)
        multiclass.set('C', different_c)
        for clf_idx, clf in enumerate(multiclass._binary_classifiers):
            self.assertEqual(clf.C, different_c[clf_idx])

    def test_apply_method(self):

        multiclass = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                              class_weight='balanced')
        multiclass.fit(self.dataset)
        multiclass.apply_method(CClassifierSVM.set, param_name='C',
                                param_value=150)

        for i in range(multiclass.num_classifiers):
            self.assertEqual(multiclass._binary_classifiers[i].C, 150)

    def test_normalization(self):
        """Test data normalization inside CClassifierMulticlassOVA."""
        from secml.ml.features.normalization import CNormalizerMinMax
        from secml.data import CDataset

        ds_norm_x = CNormalizerMinMax().fit_transform(self.dataset.X)

        multi_nonorm = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                                class_weight='balanced')
        multi_nonorm.fit(CDataset(ds_norm_x, self.dataset.Y))
        pred_y_nonorm = multi_nonorm.predict(ds_norm_x)

        multi = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                         class_weight='balanced',
                                         preprocess='min-max')
        multi.fit(self.dataset)
        pred_y = multi.predict(self.dataset.X)

        self.logger.info(
            "Predictions with internal norm:\n{:}".format(pred_y))
        self.logger.info(
            "Predictions with external norm:\n{:}".format(pred_y_nonorm))

        self.assertFalse((pred_y_nonorm != pred_y).any())

    def test_plot_decision_function(self):
        """Test plot of multiclass classifier decision function."""
        # generate synthetic data
        ds = CDLRandom(n_classes=3, n_features=2, n_redundant=0,
                       n_clusters_per_class=1, class_sep=1,
                       random_state=0).load()

        multiclass = CClassifierMulticlassOVA(
            classifier=CClassifierSVM,
            class_weight='balanced',
            preprocess='min-max')

        # Training and classification
        multiclass.fit(ds)
        y_pred, score_pred = multiclass.predict(
            ds.X, return_decision_function=True)

        def plot_hyperplane(img, clf, min_v, max_v, linestyle, label):
            """Plot the hyperplane associated to the OVA clf."""
            xx = CArray.linspace(
                min_v - 5, max_v + 5)  # make sure the line is long enough
            # get the separating hyperplane
            yy = -(clf.w[0] * xx + clf.b) / clf.w[1]
            img.sp.plot(xx, yy, linestyle, label=label)

        fig = CFigure(height=7, width=8)
        fig.sp.title('{:} ({:})'.format(multiclass.__class__.__name__,
                                        multiclass.classifier.__name__))

        x_bounds, y_bounds = ds.get_bounds()

        styles = ['go-', 'yp--', 'rs-.', 'bD--', 'c-.', 'm-', 'y-.']

        for c_idx, c in enumerate(ds.classes):
            # Plot boundary and predicted label for each OVA classifier

            plot_hyperplane(fig, multiclass._binary_classifiers[c_idx],
                            x_bounds[0], x_bounds[1], styles[c_idx],
                            'Boundary\nfor class {:}'.format(c))

            fig.sp.scatter(ds.X[ds.Y == c, 0],
                           ds.X[ds.Y == c, 1],
                           s=40, c=styles[c_idx][0])
            fig.sp.scatter(ds.X[y_pred == c, 0], ds.X[y_pred == c, 1], s=160,
                           edgecolors=styles[c_idx][0],
                           facecolors='none', linewidths=2)

        # Plotting multiclass decision function
        fig.switch_sptype('function')
        fig.sp.plot_fobj(lambda x: multiclass.predict(x),
                         grid_limits=ds.get_bounds(offset=5), colorbar=False,
                         n_grid_points=50, plot_levels=False)

        fig.sp.xlim(x_bounds[0] - .5 * x_bounds[1],
                    x_bounds[1] + .5 * x_bounds[1])
        fig.sp.ylim(y_bounds[0] - .5 * y_bounds[1],
                    y_bounds[1] + .5 * y_bounds[1])

        fig.sp.legend(loc=4)  # lower, right

        fig.show()

    def test_fun(self):
        """Test for decision_function() and predict() methods."""
        self.logger.info(
            "Test for decision_function() and predict() methods.")

        def _check_df_scores(s, n_samples):
            self.assertEqual(type(s), CArray)
            self.assertTrue(s.isdense)
            self.assertEqual(1, s.ndim)
            self.assertEqual((n_samples,), s.shape)
            self.assertEqual(float, s.dtype)

        def _check_classify_scores(l, s, n_samples, n_classes):
            self.assertEqual(type(l), CArray)
            self.assertEqual(type(s), CArray)
            self.assertTrue(l.isdense)
            self.assertTrue(s.isdense)
            self.assertEqual(1, l.ndim)
            self.assertEqual(2, s.ndim)
            self.assertEqual((n_samples,), l.shape)
            self.assertEqual((n_samples, n_classes), s.shape)
            self.assertEqual(int, l.dtype)
            self.assertEqual(float, s.dtype)

        mc = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                      class_weight='balanced')

        mc.fit(self.dataset, n_jobs=2)

        x = x_norm = self.dataset.X
        p = p_norm = self.dataset.X[0, :].ravel()

        # Transform data if a preprocess is defined
        if mc.preprocess is not None:
            x_norm = mc.preprocess.transform(x)
            p_norm = mc.preprocess.transform(p)

        # Testing decision_function on multiple points

        df_scores_0 = mc.decision_function(x, y=0)
        self.logger.info(
            "decision_function(x, y=0):\n{:}".format(df_scores_0))
        _check_df_scores(df_scores_0, self.dataset.num_samples)

        df_scores_1 = mc.decision_function(x, y=1)
        self.logger.info(
            "decision_function(x, y=1):\n{:}".format(df_scores_1))
        _check_df_scores(df_scores_1, self.dataset.num_samples)

        df_scores_2 = mc.decision_function(x, y=2)
        self.logger.info(
            "decision_function(x, y=2):\n{:}".format(df_scores_2))
        _check_df_scores(df_scores_2, self.dataset.num_samples)

        # Testing _decision_function on multiple points

        ds_priv_scores_0 = mc._decision_function(x_norm, y=0)
        self.logger.info("_decision_function(x_norm, y=0):\n"
                         "{:}".format(ds_priv_scores_0))
        _check_df_scores(ds_priv_scores_0, self.dataset.num_samples)

        ds_priv_scores_1 = mc._decision_function(x_norm, y=1)
        self.logger.info("_decision_function(x_norm, y=1):\n"
                         "{:}".format(ds_priv_scores_1))
        _check_df_scores(ds_priv_scores_1, self.dataset.num_samples)

        ds_priv_scores_2 = mc._decision_function(x_norm, y=2)
        self.logger.info("_decision_function(x_norm, y=2):\n"
                         "{:}".format(ds_priv_scores_2))
        _check_df_scores(ds_priv_scores_2, self.dataset.num_samples)

        # Comparing output of public and private

        self.assertFalse((df_scores_0 != ds_priv_scores_0).any())
        self.assertFalse((df_scores_1 != ds_priv_scores_1).any())
        self.assertFalse((df_scores_2 != ds_priv_scores_2).any())

        # Testing predict on multiple points

        labels, scores = mc.predict(x, return_decision_function=True)
        self.logger.info(
            "predict(x):\nlabels: {:}\nscores:{:}".format(labels, scores))
        _check_classify_scores(
            labels, scores, self.dataset.num_samples, mc.n_classes)

        # Comparing output of decision_function and predict

        self.assertFalse((df_scores_0 != scores[:, 0].ravel()).any())
        self.assertFalse((df_scores_1 != scores[:, 1].ravel()).any())
        self.assertFalse((df_scores_2 != scores[:, 2].ravel()).any())

        # Testing decision_function on single point

        df_scores_0 = mc.decision_function(p, y=0)
        self.logger.info(
            "decision_function(p, y=0):\n{:}".format(df_scores_0))
        _check_df_scores(df_scores_0, 1)

        df_scores_1 = mc.decision_function(p, y=1)
        self.logger.info(
            "decision_function(p, y=1):\n{:}".format(df_scores_1))
        _check_df_scores(df_scores_1, 1)

        df_scores_2 = mc.decision_function(p, y=2)
        self.logger.info(
            "decision_function(p, y=2):\n{:}".format(df_scores_2))
        _check_df_scores(df_scores_2, 1)

        # Testing _decision_function on single point

        df_priv_scores_0 = mc._decision_function(p_norm, y=0)
        self.logger.info("_decision_function(p_norm, y=0):\n{:}"
                         "".format(df_priv_scores_0))
        _check_df_scores(df_priv_scores_0, 1)

        df_priv_scores_1 = mc._decision_function(p_norm, y=1)
        self.logger.info("_decision_function(p_norm, y=1):\n{:}"
                         "".format(df_priv_scores_1))
        _check_df_scores(df_priv_scores_1, 1)

        df_priv_scores_2 = mc._decision_function(p_norm, y=2)
        self.logger.info("_decision_function(p_norm, y=2):\n"
                         "{:}".format(df_priv_scores_2))
        _check_df_scores(df_priv_scores_2, 1)

        # Comparing output of public and private

        self.assertFalse((df_scores_0 != df_priv_scores_0).any())
        self.assertFalse((df_scores_1 != df_priv_scores_1).any())
        self.assertFalse((df_scores_2 != df_priv_scores_2).any())

        self.logger.info("Testing predict on single point")

        labels, scores = mc.predict(p, return_decision_function=True)
        self.logger.info(
            "predict(p):\nlabels: {:}\nscores: {:}".format(labels, scores))
        _check_classify_scores(labels, scores, 1, mc.n_classes)

        # Comparing output of decision_function and predict

        self.assertFalse(
            (df_scores_0 != CArray(scores[:, 0]).ravel()).any())
        self.assertFalse(
            (df_scores_1 != CArray(scores[:, 1]).ravel()).any())
        self.assertFalse(
            (df_scores_2 != CArray(scores[:, 2]).ravel()).any())

    def test_gradient(self):
        """Unittests for gradient() function."""
        multiclass = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                              class_weight='balanced')
        multiclass.fit(self.dataset)

        import random
        pattern = CArray(random.choice(self.dataset.X.get_data()))
        self.logger.info("Randomly selected pattern:\n%s", str(pattern))

        # Compare with numerical gradient
        self._test_gradient_numerical(multiclass, pattern)

        # Check if we can return the i_th classifier
        for i in range(multiclass.num_classifiers):

            ova_grad = multiclass._binary_classifiers[i].gradient_f_x(pattern)

            gradient = multiclass.gradient_f_x(pattern, y=i)
            self.logger.info(
                "Gradient of {:}^th sub-clf is:\n{:}".format(i, gradient))

            self.assertFalse((gradient != ova_grad).any())

        with self.assertRaises(ValueError):
            multiclass.gradient_f_x(pattern, y=-1)
        with self.assertRaises(ValueError):
            multiclass.gradient_f_x(pattern, y=100)

    def test_preprocess(self):
        """Test classifier with preprocessors inside."""
        multiclass = CClassifierMulticlassOVA(classifier=CClassifierSVM,
                                              class_weight='balanced')

        # All linear transformations with gradient implemented
        self._test_preprocess(self.dataset, multiclass,
                              ['min-max', 'mean-std'],
                              [{'feature_range': (-1, 1)}, {}])
        self._test_preprocess_grad(self.dataset, multiclass,
                                   ['min-max', 'mean-std'],
                                   [{'feature_range': (-1, 1)}, {}])

        # Mixed linear/nonlinear transformations without gradient
        self._test_preprocess(
            self.dataset, multiclass, ['pca', 'unit-norm'], [{}, {}])


if __name__ == '__main__':
    CClassifierTestCases.main()
