import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from src.utils import clean_text, parse_installment, parse_reviews_count

logger = logging.getLogger(__name__)

def parse_product_card(card, base_url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    raw_data = {}
    raw_data["product_guid"] = card.get(selectors.get("product_guid_attr", "data-product"))
    raw_data["product_code"] = card.get(selectors.get("product_code_attr", "data-code"))
    raw_data["product_url"] = _extract_product_url(card, base_url, selectors)
    raw_data["title_raw"] = _extract_title(card, selectors)
    raw_data["img_url"] = _extract_image_url(card, selectors)
    raw_data.update(_extract_prices(card, selectors))
    raw_data.update(_extract_rating_info(card, selectors))
    raw_data["availability"] = _extract_availability(card, selectors)
    raw_data["discount"] = _extract_discount(card, selectors)
    return raw_data

def _extract_product_url(card, base_url: str, selectors: Dict[str, str]) -> Optional[str]:
    link = card.select_one(selectors.get("product_link_primary") or "")
    if not link: link = card.select_one(selectors.get("product_link_alt") or "")
    href = link.get("href") if link else None
    return urljoin(base_url, href) if href else None

def _extract_title(card, selectors: Dict[str, str]) -> str:
    title = None
    span_sel = selectors.get("product_title_span")
    if span_sel:
        title_el = card.select_one(span_sel)
        if title_el: title = title_el.get_text(" ", strip=True)
    if not title:
        link = card.select_one(selectors.get("product_link_primary") or "")
        if link: title = link.get_text(" ", strip=True)
    return clean_text(title) if title else ""

def _extract_image_url(card, selectors: Dict[str, str]) -> Optional[str]:
    img = card.select_one(selectors.get("product_image") or "")
    if img: return img.get("data-src") or img.get("src") or img.get("data-srcset")
    return None

def _extract_prices(card, selectors: Dict[str, str]) -> Dict[str, Any]:
    prices = {}
    price_el = card.select_one(selectors.get("current_price") or "")
    if price_el:
        current_text = price_el.get_text(" ", strip=True)
        old_el = price_el.select_one(".product-buy__prev")
        old_text = old_el.get_text(" ", strip=True) if old_el else ""
        clean_current = current_text.replace(old_text, "").strip()
        prices["price"] = _parse_price_to_int(clean_current)
        prices["old_price"] = _parse_price_to_int(old_text) if old_text else None
    inst_el = card.select_one(selectors.get("installment_price") or "")
    if inst_el:
        inst_text = inst_el.get_text(" ", strip=True)
        monthly, clean_text = parse_installment(inst_text)
        prices["installment_monthly"] = monthly
        prices["installment"] = clean_text
    return prices

def _extract_rating_info(card, selectors: Dict[str, str]) -> Dict[str, Any]:
    rating_info = {}
    rating_el = card.select_one(selectors.get("rating_value") or "")
    if rating_el:
        try:
            rating_text = rating_el.get_text().strip()
            clean_rating = re.sub(r'[^\d,\.]', '', rating_text).replace(',', '.')
            rating_info["rating"] = float(clean_rating) if clean_rating else None
        except (ValueError, TypeError): rating_info["rating"] = None
    rb = card.select_one(selectors.get("rating_block") or "")
    if rb:
        rb_text = rb.get_text(" ", strip=True)
        rating_info["reviews_count"] = parse_reviews_count(rb_text)
    return rating_info

def _extract_availability(card, selectors: Dict[str, str]) -> Optional[str]:
    av_el = card.select_one(selectors.get("availability") or "")
    return clean_text(av_el.get_text(" ", strip=True)) if av_el else None

def _extract_discount(card, selectors: Dict[str, str]) -> Optional[str]:
    disc_el = card.select_one(selectors.get("discount") or "")
    return clean_text(disc_el.get_text(" ", strip=True)) if disc_el else None

def _parse_price_to_int(price_text: str) -> Optional[int]:
    if not price_text: return None
    digits = re.sub(r'[^\d]', '', price_text)
    return int(digits) if digits else None