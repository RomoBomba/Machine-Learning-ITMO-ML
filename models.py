import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.tree import DecisionTreeClassifier

class BaselineModel:
    def predict(self, X):
        predictions = []
        for _, row in X.iterrows():
            price = row['price']
            ram = row.get('ram_gb', 4)
            storage = row.get('storage_gb', 64)
            camera = row.get('max_camera_mp', 12)
            rating = row.get('rating', 4.0)
            value_ratio = (ram * 1000 + storage * 50 + camera * 100) / price * (rating / 5.0)
            if value_ratio > 0.3:
                pred = 'exceptional_value'
            elif value_ratio > 0.2:
                pred = 'great_value'
            elif value_ratio > 0.1:
                pred = 'good_value'
            elif value_ratio > 0.05:
                pred = 'average_value'
            else:
                pred = 'poor_value'
            predictions.append(pred)
        return np.array(predictions)

class CustomRandomForest(BaseEstimator, ClassifierMixin):
    def __init__(self, n_estimators=10, max_depth=5, min_samples_split=2):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees = []
        self.classes_ = None
    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self.trees = []
        n_samples = X.shape[0]

        print(f"Обучаем кастомный Random Forest с {self.n_estimators} деревьями...")

        for i in range(self.n_estimators):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_bootstrap = X.iloc[indices] if hasattr(X, 'iloc') else X[indices]
            y_bootstrap = y.iloc[indices] if hasattr(y, 'iloc') else y[indices]
            tree = DecisionTreeClassifier(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=42 + i
            )
            tree.fit(X_bootstrap, y_bootstrap)
            self.trees.append(tree)
            if (i + 1) % 5 == 0:
                print(f"  Обучено {i + 1}/{self.n_estimators} деревьев")
        return self

    def predict(self, X):
        if not self.trees:
            raise ValueError("Модель не обучена. Сначала вызовите fit().")
        all_predictions = []
        for i, tree in enumerate(self.trees):
            pred = tree.predict(X)
            all_predictions.append(pred)
        predictions_array = np.array(all_predictions)
        final_predictions = []
        for sample_idx in range(X.shape[0]):
            sample_predictions = predictions_array[:, sample_idx]
            unique, counts = np.unique(sample_predictions, return_counts=True)
            winner = unique[np.argmax(counts)]
            final_predictions.append(winner)
        return np.array(final_predictions)

    def predict_proba(self, X):
        if not self.trees:
            raise ValueError("Модель не обучена. Сначала вызовите fit().")
        all_predictions = []
        for tree in self.trees:
            pred = tree.predict(X)
            all_predictions.append(pred)
        predictions_array = np.array(all_predictions)
        probas = []
        for sample_idx in range(X.shape[0]):
            sample_predictions = predictions_array[:, sample_idx]
            class_probs = []
            for class_label in self.classes_:
                count = np.sum(sample_predictions == class_label)
                prob = count / len(self.trees)
                class_probs.append(prob)
            probas.append(class_probs)
        return np.array(probas)