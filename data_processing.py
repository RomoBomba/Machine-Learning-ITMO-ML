import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

class DataProcessor:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()

    def load_data(self, filepath):
        print("Загружаем данные...")
        df = pd.read_csv(filepath)
        print(f"Загружено {len(df)} записей")
        return df

    def clean_data(self, df):
        print("Очищаем данные...")
        df_clean = df.copy()
        numeric_columns = {
            'old_price': df_clean['price'],
            'battery_mah': df_clean['battery_mah'].median(),
            'rating': df_clean['rating'].median(),
            'reviews_count': 0,
            'ram_gb': df_clean['ram_gb'].median(),
            'storage_gb': df_clean['storage_gb'].median(),
            'diagonal_in': df_clean['diagonal_in'].median(),
            'num_cameras': df_clean['num_cameras'].median(),
            'max_camera_mp': df_clean['max_camera_mp'].median()
        }

        for column, fill_value in numeric_columns.items():
            if column in df_clean.columns:
                before = df_clean[column].isna().sum()
                df_clean[column] = df_clean[column].fillna(fill_value)
                after = df_clean[column].isna().sum()
                print(f"  {column}: заполнено {before - after} пропусков")
        text_columns = ['color', 'screen_type', 'resolution']
        for column in text_columns:
            if column in df_clean.columns:
                df_clean[column] = df_clean[column].fillna('unknown')

        binary_columns = ['has_nfc', 'has_5g']
        for column in binary_columns:
            if column in df_clean.columns:
                df_clean[column] = df_clean[column].fillna(0).astype(int)
        print("Очистка данных завершена")
        return df_clean

    def extract_features_from_specs(self, df):
        print("Извлекаем признаки из specs_raw...")
        df_extracted = df.copy()
        df_extracted['processor_cores'] = df_extracted['specs_raw'].str.extract(r'ядер - (\d+)')[0]
        df_extracted['processor_cores'] = df_extracted['processor_cores'].fillna(4).astype(int)
        df_extracted['sim_count'] = df_extracted['specs_raw'].str.extract(r'(\d) SIM')[0]
        df_extracted['sim_count'] = df_extracted['sim_count'].fillna(1).astype(int)
        freq_matches = df_extracted['specs_raw'].str.extract(r'(\d+\.?\d*) ГГц')
        if not freq_matches.empty:
            df_extracted['max_freq_ghz'] = freq_matches[0].fillna(2.0).astype(float)
        else:
            df_extracted['max_freq_ghz'] = 2.0
        print(f"Извлечено {df_extracted['processor_cores'].nunique()} уникальных значений ядер процессора")
        print(f"Извлечено {df_extracted['sim_count'].nunique()} уникальных значений SIM-карт")
        return df_extracted

    def create_new_features(self, df):
        print("Создаем новые признаки...")
        df_new = df.copy()
        df_new['discount_percent'] = np.where(
            df_new['old_price'] > df_new['price'],
            (df_new['old_price'] - df_new['price']) / df_new['old_price'] * 100,
            0
        )
        def calculate_pixel_density(resolution, diagonal):
            if pd.isna(resolution) or pd.isna(diagonal):
                return 400
            try:
                if 'x' in str(resolution):
                    width, height = map(int, str(resolution).split('x'))
                    diagonal_pixels = np.sqrt(width ** 2 + height ** 2)
                    return diagonal_pixels / diagonal
                else:
                    return 400
            except:
                return 400
        df_new['pixel_density'] = df_new.apply(
            lambda row: calculate_pixel_density(row['resolution'], row['diagonal_in']),
            axis=1
        )
        df_new['log_price'] = np.log1p(df_new['price'])
        df_new['features_score'] = (
                df_new['ram_gb'] * 1000 + df_new['storage_gb'] * 50 + df_new['max_camera_mp'] * 100 +
                df_new['battery_mah'] * 0.1 + (df_new['has_5g'] * 1000 if 'has_5g' in df_new.columns else 0)
        )
        df_new['price_per_feature'] = df_new['price'] / (df_new['features_score'] + 1)

        print("Создание признаков завершено")
        return df_new

    def prepare_for_training(self, df, target_column='value_category'):
        print("Подготавливаем данные для ML...")
        categorical_features = ['brand', 'color', 'screen_type', 'price_segment']

        numeric_features = [
            'price', 'old_price', 'diagonal_in', 'ram_gb', 'storage_gb',
            'battery_mah', 'num_cameras', 'max_camera_mp', 'rating',
            'reviews_count', 'has_nfc', 'has_5g', 'discount_percent',
            'pixel_density', 'log_price', 'processor_cores', 'sim_count',
            'max_freq_ghz', 'features_score', 'price_per_feature'
        ]
        existing_numeric = [f for f in numeric_features if f in df.columns]
        existing_categorical = [f for f in categorical_features if f in df.columns]
        print(f"Используем {len(existing_numeric)} числовых признаков")
        print(f"Используем {len(existing_categorical)} категориальных признаков")

        X_categorical = pd.DataFrame()
        for feature in existing_categorical:
            le = LabelEncoder()
            X_categorical[feature] = le.fit_transform(df[feature].astype(str))
            self.label_encoders[feature] = le
        X_numeric = df[existing_numeric]
        X = pd.concat([X_numeric, X_categorical], axis=1)
        y = df[target_column]
        print(f"Финальный размер признаков: {X.shape}")
        print(f"Целевая переменная: {y.nunique()} классов")
        return X, y

    def get_feature_names(self):
        return [f for f in self.label_encoders.keys()] + [
            'price', 'old_price', 'diagonal_in', 'ram_gb', 'storage_gb',
            'battery_mah', 'num_cameras', 'max_camera_mp', 'rating',
            'reviews_count', 'has_nfc', 'has_5g', 'discount_percent',
            'pixel_density', 'log_price', 'processor_cores', 'sim_count',
            'max_freq_ghz', 'features_score', 'price_per_feature'
        ]

    def create_target_variable(self, df):
        print("Создаем целевую переменную value_category...")

        def calculate_value_score(row):
            price = row['price']
            old_price = row.get('old_price', price)
            rating = row.get('rating', 4.0)
            ram = row.get('ram_gb', 4)
            storage = row.get('storage_gb', 64)
            max_camera_mp = row.get('max_camera_mp', 12)
            has_5g = row.get('has_5g', 0)
            battery_mah = row.get('battery_mah', 4000)
            base_features = (
                    ram * 8.0 +
                    storage * 0.3 +
                    battery_mah * 0.0015
            )
            extra_features = (
                    max_camera_mp * 0.4 +
                    (10 if has_5g else 0)
            )
            total_features = base_features + extra_features
            discount_factor = 1.0
            if old_price > price:
                discount_percent = (old_price - price) / old_price
                discount_factor = 1 + min(discount_percent * 0.15, 0.2)
            rating_factor = 0.6 + (rating - 3) * 0.1 if rating else 0.7
            brand_factor = 1.0
            if row.get('brand') == 'Apple':
                brand_factor = 0.9
            price_factor = np.log(max(price, 10000))
            value_score = (total_features * discount_factor * rating_factor * brand_factor * 800) / price_factor
            return value_score

        def create_categories(value_scores):
            p25 = value_scores.quantile(0.25)
            p50 = value_scores.quantile(0.50)
            p75 = value_scores.quantile(0.75)
            p90 = value_scores.quantile(0.90)
            categories = ['poor_value', 'average_value', 'good_value', 'great_value', 'exceptional_value']
            return pd.cut(value_scores, bins=[-np.inf, p25, p50, p75, p90, np.inf],
                          labels=categories, include_lowest=True)
        df_with_target = df.copy()
        df_with_target['value_score'] = df_with_target.apply(calculate_value_score, axis=1)
        df_with_target['value_category'] = create_categories(df_with_target['value_score'])
        print("Целевая переменная создана:")
        print(df_with_target['value_category'].value_counts())
        return df_with_target