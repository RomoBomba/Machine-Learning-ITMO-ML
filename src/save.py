import csv
import logging
from pathlib import Path
from typing import List
from src.models import Product

logger = logging.getLogger(__name__)

class DataSaver:
    def __init__(self, config: dict):
        self.config = config
        self.output_cfg = config["OUTPUT"]

    def save_to_csv(self, products: List[Product]):
        if not products:
            logger.warning("Нет данных для сохранения")
            return
        output_path = Path(self.output_cfg["dataset_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not products:
            logger.warning("Нет продуктов для сохранения")
            return
        sample_record = products[0].to_record()
        fieldnames = list(sample_record.keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for product in products:
                writer.writerow(product.to_record())

        logger.info(f"Сохранено {len(products)} записей в {output_path}")
        self._save_sample(products)

    def _save_sample(self, products: List[Product], sample_size: int = 10):
        sample_path = Path(self.output_cfg["sample_path"])
        sample_products = products[:sample_size]

        if not sample_products:
            return
        sample_record = sample_products[0].to_record()
        fieldnames = list(sample_record.keys())
        with open(sample_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for product in sample_products:
                writer.writerow(product.to_record())
        logger.info(f"Сохранен пример из {len(sample_products)} записей в {sample_path}")