# !/usr/bin/env python3
import logging
from pathlib import Path
import yaml
from bs4 import BeautifulSoup
from src.parser import parse_product_card
from src.models import Product
from src.save import DataSaver

def load_config():
    ROOT = Path(__file__).parent
    CONFIG_PATH = ROOT / "config.yaml"
    with open(CONFIG_PATH, "r", encoding="utf-8") as f: return yaml.safe_load(f)

def main():
    config = load_config()
    logging.basicConfig(
        level=config["LOGGING"]["level"],
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    html_file_path = Path("html_samples/DNS_smartphones_71.html")
    if not html_file_path.exists():
        logger.error(f"HTML файл не найден: {html_file_path}")
        return

    logger.info(f"Чтение HTML файла: {html_file_path}")
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "lxml")
    selectors = config["SELECTORS"]
    base_url = config["BASE_URL"]
    cards = soup.select(selectors["product_card"])
    logger.info(f"Найдено {len(cards)} карточек товаров")
    records = []
    for i, card in enumerate(cards):
        try:
            raw_data = parse_product_card(card, base_url, selectors)
            records.append(raw_data)
            if i % 50 == 0 and i > 0: logger.info(f"Обработано {i}/{len(cards)} карточек")
        except Exception as e:
            logger.error(f"Ошибка парсинга карточки {i}: {e}")
            continue

    logger.info("Преобразование данных в объекты Product...")
    products = []
    for i, raw_data in enumerate(records):
        try:
            product = Product.from_catalog_record(raw_data)
            products.append(product)
        except Exception as e:
            logger.error(f"Ошибка создания продукта {i}: {e}")
            continue

    logger.info(f"Сохранение {len(products)} товаров...")
    saver = DataSaver(config)
    saver.save_to_csv(products)
    logger.info("Готово! Проверьте папку dataset/")


if __name__ == "__main__":
    main()