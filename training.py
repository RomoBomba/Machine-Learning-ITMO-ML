from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

class ModelTrainer:
    def __init__(self, test_size=0.2, val_size=0.2, random_state=42):
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state

    def split_data(self, X, y):
        print("Разделяем данные на train/validation/test...")

        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            stratify=y,
            random_state=self.random_state
        )
        val_size_adjusted = self.val_size / (1 - self.test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size_adjusted,
            stratify=y_temp,
            random_state=self.random_state
        )
        print(f"Train set: {X_train.shape[0]} samples")
        print(f"Validation set: {X_val.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        return X_train, X_val, X_test, y_train, y_val, y_test

    def train_baseline(self, X_val, y_val):
        print("\n=== ОБУЧЕНИЕ BASELINE МОДЕЛИ ===")
        from models import BaselineModel
        baseline = BaselineModel()
        y_pred_baseline = baseline.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred_baseline)
        print(f"Baseline Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_val, y_pred_baseline))
        return baseline, y_pred_baseline

    def train_sklearn_model(self, X_train, X_val, y_train, y_val, model_type='random_forest'):
        print(f"\n=== ОБУЧЕНИЕ SKLEARN {model_type.upper()} ===")
        if model_type == 'random_forest':
            model = RandomForestClassifier(random_state=self.random_state)
            param_grid = {
                'n_estimators': [50, 100],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5]
            }
        else:
            raise ValueError(f"Неизвестный тип модели: {model_type}")
        print("Подбираем гиперпараметры...")
        grid_search = GridSearchCV(
            model, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1
        )
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_val)

        print(f"Лучшие параметры: {grid_search.best_params_}")
        print(f"Validation Accuracy: {accuracy_score(y_val, y_pred):.4f}")
        print("\nClassification Report:")
        print(classification_report(y_val, y_pred))
        return best_model, y_pred, grid_search.best_params_

    def train_custom_model(self, X_train, X_val, y_train, y_val):
        print("\n=== ОБУЧЕНИЕ КАСТОМНОЙ МОДЕЛИ ===")

        from models import CustomRandomForest
        best_score = 0
        best_model = None
        best_params = {}
        best_predictions = None

        param_combinations = [
            {'n_estimators': 10, 'max_depth': 5},
            {'n_estimators': 20, 'max_depth': 7},
            {'n_estimators': 30, 'max_depth': 10},
        ]
        for params in param_combinations:
            print(f"Пробуем параметры: {params}")
            model = CustomRandomForest(
                n_estimators=params['n_estimators'],
                max_depth=params['max_depth'],
                min_samples_split=2
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            score = accuracy_score(y_val, y_pred)
            print(f"  Accuracy: {score:.4f}")
            if score > best_score:
                best_score = score
                best_model = model
                best_params = params
                best_predictions = y_pred
        print(f"Лучшие параметры: {best_params}")
        print(f"Лучшая Accuracy: {best_score:.4f}")
        print("\nClassification Report для лучшей модели:")
        print(classification_report(y_val, best_predictions))
        return best_model, best_predictions, best_params