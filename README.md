# Machine-Learning-ITMO-ML
Machine learning course. ML ITMO IS27. Labs and theormins.

# Парсер смартфонов DNS Shop - Лабораторная работа по парсингу

## О проекте

Данный проект представляет собой парсер для сбора данных о смартфонах с сайта DNS Shop. Изначально разрабатывался для онлайн-парсинга, но из-за блокировок со стороны сайта был адаптирован для работы с локально сохраненными HTML-страницами.

### Цели лабораторной работы
- Собрать датасет из 1000+ записей
- Извлечь минимум 6 переменных разных типов
- Создать нетривиальный таргет для прогнозирования
- Реализовать краулинг и парсинг данных

#### Ссылка на датасет: [Тык](https://disk.yandex.ru/d/tmpj5kiB_04r6A)
    
## Проблема с онлайн-парсингом

DNS Shop активно блокирует парсинг через механизмы защиты. При попытке онлайн-парсинга возникают ошибки:

```log
2025-09-27 23:32:18,496 - __main__ - INFO - === Запуск парсера DNS ===
2025-09-27 23:32:18,498 - __main__ - INFO - Этап 1: Сбор данных с каталога...
2025-09-27 23:32:18,498 - src.crawler - INFO - Обработка страницы 1: https://www.dns-shop.ru/catalog/17a89aab16404e77/smartfony/
2025-09-27 23:32:19,167 - src.crawler - WARNING - GET https://www.dns-shop.ru/catalog/17a89aab16404e77/smartfony/ -> status 401 (attempt 1/3)
2025-09-27 23:32:20,693 - src.crawler - WARNING - GET https://www.dns-shop.ru/catalog/17a89aab16404e77/smartfony/ -> status 401 (attempt 2/3)
2025-09-27 23:32:22,717 - src.crawler - WARNING - GET https://www.dns-shop.ru/catalog/17a89aab16404e77/smartfony/ -> status 401 (attempt 3/3)
2025-09-27 23:32:25,227 - src.crawler - ERROR - Ошибка при обработке страницы 1: Failed to fetch https://www.dns-shop.ru/catalog/17a89aab16404e77/smartfony/ after 3 attempts
2025-09-27 23:32:25,227 - src.crawler - INFO - Собрано 0 записей с каталога
2025-09-27 23:32:25,230 - __main__ - INFO - Этап 2: Парсинг 0 товаров...
2025-09-27 23:32:25,230 - __main__ - INFO - Этап 3: Сохранение 0 товаров...
2025-09-27 23:32:25,231 - src.save - WARNING - Нет данных для сохранения
2025-09-27 23:32:25,231 - __main__ - INFO - === Парсинг завершен успешно! ===
```

**Статус 401 (Unauthorized)** указывает на то, что DNS Shop распознал парсинг и блокирует запросы.

### Решение: Локальный парсинг
Проект адаптирован для работы с предварительно сохраненными HTML-страницами, что полностью соответствует условиям лабораторной работы.

## Структура проекта

```
dns-parser/
├── test_catalog.py         # Основной скрипт тестирования
├── config.yaml             # Конфигурация парсера
├── requirements.txt        # Зависимости проекта
├── html_samples/           # Локальные HTML-файлы
│   └── DNS_smartphones_71.html
├── src/                    # Исходный код
│   ├── parser.py           # Парсинг HTML-карточек
│   ├── models.py           # Модели данных и таргеты
│   ├── utils.py            # Вспомогательные функции
│   └── save.py             # Сохранение в CSV
└── dataset/                # Результаты парсинга
    ├── dataset.csv         # Полный датасет (1262 записи)
    └── sample.csv          # Пример данных (10 записей)
```

## Уникальный таргет: Индекс ценности покупки

### Особенный подход к оценке смартфонов

Вместо простого прогнозирования цены или категории, был разработан **композитный таргет "Индекс ценности покупки" (Value Score)**, который оценивает соотношение характеристик телефона к его стоимости.

### Формула расчета Value Score:

```python
def calculate_value_score(price, old_price, rating, ram, storage, max_camera_mp, has_5g):
    # 1. Фактор характеристик
    feature_score = (ram * 1000 + storage * 50 + max_camera_mp * 100 + 
                    (1000 if has_5g else 0))
    
    # 2. Фактор скидки
    discount_factor = 1.0
    if old_price and old_price > price:
        discount_factor = 1 + (old_price - price) / old_price
    
    # 3. Фактор рейтинга
    rating_factor = (rating - 3) / 2 if rating else 0.5
    
    # Итоговый score
    value_score = discount_factor * (feature_score / price) * rating_factor
    return value_score
```

### Категоризация по Value Score:

| Value Score | Категория | Описание |
|------------|-----------|----------|
| ≥ 0.3 | exceptional_value | Исключительная ценность |
| 0.2-0.3 | great_value | Отличная ценность |
| 0.1-0.2 | good_value | Хорошая ценность |
| 0.05-0.1 | average_value | Средняя ценность |
| < 0.05 | poor_value | Низкая ценность |

## Пример данных из датасета (10 записей)

| product_url | brand | model | price | price_segment | value_score | value_category | rating | storage_gb | ram_gb | diagonal_in | battery_mah | num_cameras | has_5g |
|-------------|-------|-------|-------|---------------|-------------|----------------|--------|------------|--------|-------------|-------------|-------------|--------|
| [iPhone 16 Pro Max](https://www.dns-shop.ru/product/308735c56f27d0a4/69-smartfon-apple-iphone-16-pro-max-256-gb-cernyj/) | Apple | iPhone 16 Pro Max | 127,399₽ | flagship | 0.218 | great_value | 4.74 | 256 | 8 | 6.9" | - | 3 | ✅ |
| [Samsung S25 Ultra](https://www.dns-shop.ru/product/02247015da15d582/69-smartfon-samsung-galaxy-s25-ultra-256-gb-cernyj/) | Samsung | Galaxy S25 Ultra | 88,999₽ | flagship | 0.473 | exceptional_value | 4.84 | 256 | 12 | 6.9" | 5000 | 4 | ✅ |
| [iPhone 15](https://www.dns-shop.ru/product/00eb38374882ed20/61-smartfon-apple-iphone-15-128-gb-cernyj/) | Apple | iPhone 15 | 64,199₽ | flagship | 0.289 | great_value | 4.82 | 128 | 6 | 6.1" | 3349 | 2 | ✅ |
| [Xiaomi Redmi Note 14](https://www.dns-shop.ru/product/7ffd0cf6a89cd21a/667-smartfon-xiaomi-redmi-note-14-256-gb-cernyj/) | Xiaomi | Redmi Note 14 | 19,699₽ | mid-range | 1.412 | exceptional_value | 4.76 | 256 | 8 | 6.67" | 5500 | 3 | ❌ |
| [iPhone 16 Pro](https://www.dns-shop.ru/product/ff782fea6f26d0a4/63-smartfon-apple-iphone-16-pro-256-gb-cernyj/) | Apple | iPhone 16 Pro | 118,799₽ | flagship | 0.243 | great_value | 4.81 | 256 | 8 | 6.3" | - | 3 | ✅ |
| [iPhone 16 Pro Max](https://www.dns-shop.ru/product/320772966f27d0a4/69-smartfon-apple-iphone-16-pro-max-256-gb-bezevyj/) | Apple | iPhone 16 Pro Max | 128,599₽ | flagship | 0.216 | great_value | 4.74 | 256 | 8 | 6.9" | - | 3 | ✅ |
| [Samsung S25 Ultra](https://www.dns-shop.ru/product/d4a725addc6cd582/69-smartfon-samsung-galaxy-s25-ultra-512-gb-cernyj/) | Samsung | Galaxy S25 Ultra | 104,999₽ | flagship | 0.513 | exceptional_value | 4.84 | 512 | 12 | 6.9" | 5000 | 4 | ✅ |
| [iPhone 13](https://www.dns-shop.ru/product/5c7ed98c37e3ed20/61-smartfon-apple-iphone-13-128-gb-belyj/) | Apple | iPhone 13 | 47,999₽ | flagship | 0.276 | great_value | 4.88 | 128 | 4 | 6.1" | 3240 | 2 | ✅ |
| [Samsung A56](https://www.dns-shop.ru/product/09d95e620075d9cb/67-smartfon-samsung-galaxy-a56-256-gb-cernyj/) | Samsung | Galaxy A56 | 34,999₽ | premium | 0.708 | exceptional_value | 4.85 | 256 | 8 | 6.7" | 5000 | 3 | ✅ |
| [iPhone 16 Pro](https://www.dns-shop.ru/product/01351ac06f27d0a4/63-smartfon-apple-iphone-16-pro-256-gb-bezevyj/) | Apple | iPhone 16 Pro | 118,799₽ | flagship | 0.243 | great_value | 4.81 | 256 | 8 | 6.3" | - | 3 | ✅ |

## 🔍 Анализ примеров:

### **Ценовые сегменты:**
- **Flagship** (>40,000₽): Apple iPhone 13-16, Samsung S25 Ultra
- **Premium** (20,000-40,000₽): Samsung Galaxy A56
- **Mid-range** (10,000-20,000₽): Xiaomi Redmi Note 14

### **Индекс ценности (Value Score):**
- **Исключительная ценность** (>0.3): Xiaomi Redmi Note 14 (1.412), Samsung S25 Ultra (0.473-0.513), Samsung A56 (0.708)
- **Отличная ценность** (0.2-0.3): Все модели Apple iPhone (0.216-0.289)

### **Технические характеристики:**
- **Память**: от 128 ГБ до 512 ГБ
- **Оперативная память**: от 4 ГБ до 12 ГБ  
- **Диагональ экрана**: от 6.1" до 6.9"
- **Камеры**: от 2 до 4 модулей
- **Поддержка 5G**: есть у всех кроме Xiaomi Redmi Note 14
## Результаты парсинга

### Статистика датасета
- **Всего записей**: 1262 смартфона
- **Успешных парсингов**: 1262 (100%)
- **Размер датасета**: 1.59 МБ

### Переменные датасета

| Тип | Переменные | Кол-во | Пример               |
|-----|------------|---------|----------------------|
| **Категориальные** | `brand`, `price_segment`, `value_category` | 3+ | "Apple", "premium", "great_value" |
| **Целочисленные** | `storage_gb`, `ram_gb`, `battery_mah` | 3+ | 256, 8, 5000         |
| **Дробные** | `rating`, `diagonal_in`, `value_score` | 3+ | 4.74, 6.9, 0.218     |

## Соответствие требованиям лабораторной

### Обязательные требования
- [x] **1000+ строк**: 1262 записи ✓
- [x] **2+ категориальные**: brand, price_segment, value_category ✓  
- [x] **2+ целочисленные**: storage_gb, ram_gb, battery_mah ✓
- [x] **2+ дробные**: rating, diagonal_in, value_score ✓
- [x] **Таргет**: price_segment (классификация), value_score (регрессия) ✓

### Дополнительные улучшения
- [x] **Уникальный таргет**: индекс ценности покупки ✓
- [x] **Чистая архитектура**: разделение на модули ✓
- [x] **Обработка ошибок**: устойчивость к битым данным ✓
- [x] **Логирование**: подробный процесс работы ✓

## Исследовательская ценность

### Инновационность подхода
1. **Композитный таргет** - объединение нескольких метрик в одну
2. **Адаптация к ограничениям** - переход на локальный парсинг
3. **Практическая применимость** - реальная помощь в выборе смартфона

### Возможности для исследований
- Прогнозирование ценовых сегментов
- Анализ рыночных тенденций
- Сравнение брендов по value-for-money

---
**Разработчик**: Роман Шевцов М3314  
**Курс**: Машинное обучение