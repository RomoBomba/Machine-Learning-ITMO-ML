import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

def clean_text(s: Optional[str]) -> str:
    if not s: return ""
    s = s.replace('\u200b', '').replace('\u200c', '').replace('\xa0', ' ')
    s = re.sub(r'[^\w\sА-Яа-яёЁA-Za-z0-9"«».,:+*()\[\]/\-×xº″°%]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_int_any(text: Optional[str]) -> Optional[int]:
    if not text: return None
    m = re.search(r'(\d{1,6})', text.replace('\xa0', ' '))
    return int(m.group(1)) if m else None

def extract_float(text: Optional[str]) -> Optional[float]:
    if not text: return None
    m = re.search(r'(\d+(?:[.,]\d+)?)', text)
    if not m: return None
    return float(m.group(1).replace(',', '.'))

def extract_storage(text: Optional[str]) -> Optional[int]:
    if not text: return None
    m = re.search(r'(\d+)\s*(?:ГБ|GB)\b', text, re.IGNORECASE)
    return int(m.group(1)) if m else None

def extract_battery(text: Optional[str]) -> Optional[int]:
    if not text: return None
    s = text.replace('\xa0', ' ')
    m = re.search(r'(\d{3,6})\s*(?:mAh|mah|mA\W*ch|мА\W*ч|мач|мах|мАч)\b', s, flags=re.IGNORECASE)
    if m: return int(m.group(1))
    m2 = re.search(r'(\d{3,6})\s*(?=мА|мач|аккум|батар|mAh|мах)', s, flags=re.IGNORECASE)
    if m2: return int(m2.group(1))
    return None

def extract_diag(text: Optional[str]) -> Optional[float]:
    if not text: return None
    m = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:["″]|дюйм|in)?\b', text)
    if m: return float(m.group(1).replace(',', '.'))
    return None

def extract_camera_list(text: Optional[str]) -> List[int]:
    if not text: return []
    nums = re.findall(r'(\d{1,3})(?=(?:\s*(?:Мп|MP|мп|mp))|(?=[+\s]))', text, flags=re.IGNORECASE)
    if nums: return [int(x) for x in nums]
    nums2 = re.findall(r'(\d{1,3})', text)
    return [int(x) for x in nums2] if nums2 else []

def extract_has_feature(text: Optional[str], keywords: List[str]) -> bool:
    if not text: return False
    low = text.lower()
    return any(k.lower() in low for k in keywords)

def parse_reviews_count(text: Optional[str]) -> Optional[int]:
    if not text: return None
    s = text.lower().replace('\xa0', ' ').strip()
    s = s.replace(',', '.')
    m = re.search(r'([\d\.]+)\s*(k|к|тыс|тыс\.)?\s*(?=отз)', s)
    if m:
        val = float(m.group(1))
        suf = m.group(2)
        if suf: return int(round(val * 1000))
        return int(round(val))
    candidates = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)(?:\s*(k|к|тыс|тыс\.)?)', s):
        num = float(m.group(1))
        suf = m.group(2)
        if suf: num = num * 1000
        candidates.append(int(round(num)))
    if candidates: return max(candidates)

    ints = [int(x) for x in re.findall(r'(\d{2,6})', s)]
    if ints: return max(ints)
    return None

def parse_installment(text: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    if not text: return None, None
    s = text.replace('\xa0', ' ').strip()
    m = re.search(r'(\d[\d\s]*)\s*₽', s)
    if m:
        digits = re.sub(r'\D', '', m.group(1))
        if digits:
            monthly = int(digits)
            cleaned = f"{monthly} ₽/мес"
            return monthly, cleaned
    m2 = re.search(r'(\d[\d\s]*)', s)
    if m2:
        digits = re.sub(r'\D', '', m2.group(1))
        if digits:
            monthly = int(digits)
            cleaned = f"{monthly}"
            return monthly, cleaned
    return None, clean_text(s)

def parse_smartphone_title_improved(title: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"diagonal_in": None,
        "brand": None,
        "model": None,
        "storage_gb": None,
        "color": None,
        "ram_gb": None,
        "battery_mah": None,
        "screen_type": None,
        "resolution": None,
        "camera_list_mp": [],
        "num_cameras": None,
        "max_camera_mp": None,
        "has_nfc": False,
        "has_5g": False,
        "specs_raw": None,
    }

    if not title: return result
    t = clean_text(title)
    t = re.sub(r'\bсмартфон\b', '', t, flags=re.IGNORECASE).strip()

    specs_block_match = re.search(r'\[(.*?)\]', t)
    specs_block = specs_block_match.group(1) if specs_block_match else ""
    result["specs_raw"] = specs_block
    main_part = t[:specs_block_match.start()].strip() if specs_block_match else t
    diag = extract_diag(main_part)
    result["diagonal_in"] = diag
    if diag: main_part = re.sub(r'^\s*\d+(?:[.,]\d+)?\s*(?:["″]|дюйм|in)?', '', main_part, flags=re.IGNORECASE).strip()

    storage = extract_storage(main_part)
    result["storage_gb"] = storage
    if storage:
        m = re.search(r'(\d+\s*(?:ГБ|GB))', main_part, re.IGNORECASE)
        if m:
            before = main_part[:m.start()].strip()
            after = main_part[m.end():].strip()
            if before:
                tokens = before.split()
                result["brand"] = tokens[0]
                result["model"] = " ".join(tokens[1:]) if len(tokens) > 1 else None
            if after:
                result["color"] = " ".join(after.split()[:3])
    else:
        tokens = main_part.split()
        if tokens:
            result["brand"] = tokens[0]
            result["model"] = " ".join(tokens[1:]) if len(tokens) > 1 else None

    specs = [s.strip() for s in re.split(r',\s*', specs_block) if s.strip()]
    known_screen_types = ["retina", "amoled", "oled", "ips", "lcd", "super retina", "dynamic amoled", "promotion", "super amoled"]
    for s in specs:
        sl = s.lower()
        if "ядер" in sl or "ггц" in sl:
            result.setdefault("processor", s)
            continue
        if re.search(r'\d+\s*гб', s, re.IGNORECASE):
            val = extract_int_any(s)
            if re.search(r'операт|ram', s, re.IGNORECASE):
                result["ram_gb"] = val
            else:
                if result["ram_gb"] is None and val is not None and val <= 64:
                    result["ram_gb"] = val
        if re.search(r'\d+\s*sim', s, re.IGNORECASE):
            result.setdefault("sim", s)
        if any(st in sl for st in known_screen_types):
            result["screen_type"] = s
        if re.search(r'\d{3,4}x\d{3,4}', s):
            result["resolution"] = s
        if 'мп' in sl or 'mp' in sl:
            cams = extract_camera_list(s)
            if cams:
                result["camera_list_mp"] = cams
                result["num_cameras"] = len(cams)
                result["max_camera_mp"] = max(cams)
        if re.search(r'\d{3,6}', s):
            bat = extract_battery(s)
            if bat: result["battery_mah"] = bat
        if 'nfc' in sl: result["has_nfc"] = True
        if '5g' in sl: result["has_5g"] = True

    if result["ram_gb"] is None:
        mram = re.search(r'(\d+)\s*(?:ГБ|GB)\b', main_part, re.IGNORECASE)
        if mram:
            val = int(mram.group(1))
            if val <= 64:
                result["ram_gb"] = val
    if result["camera_list_mp"] and result["num_cameras"] is None:
        result["num_cameras"] = len(result["camera_list_mp"])
    if result["camera_list_mp"] and result["max_camera_mp"] is None:
        result["max_camera_mp"] = max(result["camera_list_mp"])

    return result


def parse_price_from_card_element(price_el) -> (Optional[int], Optional[int]):
    if not price_el: return None, None
    txt = price_el.get_text(" ", strip=True)
    old_el = price_el.select_one(".product-buy__prev")
    old_price = None
    if old_el:
        old_str = old_el.get_text(" ", strip=True)
        old_price = int(re.sub(r'[^\d]', '', old_str) or 0)
        txt = txt.replace(old_str, '').strip()
    curr = int(re.sub(r'[^\d]', '', txt) or 0) if txt else None
    return (curr if curr else None, old_price if old_price else None)

def parse_product_card_bs4(card, base_url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    rec: Dict[str, Any] = {}
    rec["product_guid"] = card.get(selectors.get("product_guid_attr", "data-product"))
    rec["product_code"] = card.get(selectors.get("product_code_attr", "data-code"))
    link = card.select_one(selectors.get("product_link_primary") or "")
    if not link:
        link = card.select_one(selectors.get("product_link_alt") or "")
    href = link.get("href") if link else None
    rec["product_url"] = urljoin(base_url, href) if href else None
    title = None
    span_sel = selectors.get("product_title_span")
    if span_sel and card.select_one(span_sel):
        title = card.select_one(span_sel).get_text(" ", strip=True)
    elif link:
        title = link.get_text(" ", strip=True)
    else:
        alt = selectors.get("product_title_alt")
        if alt and card.select_one(alt): title = card.select_one(alt).get_text(" ", strip=True)
    rec["title_raw"] = clean_text(title)
    img = card.select_one(selectors.get("product_image") or "")
    if img: rec["img_url"] = img.get("data-src") or img.get("data-srcset") or img.get("src")
    else: rec["img_url"] = None
    price_el = card.select_one(selectors.get("current_price") or "")
    curr_price, old_price = parse_price_from_card_element(price_el)
    rec["price"] = curr_price
    rec["old_price"] = old_price
    inst_el = card.select_one(selectors.get("installment_price") or "")
    inst_text = inst_el.get_text(" ", strip=True) if inst_el else None
    inst_monthly, inst_clean = parse_installment(inst_text)
    rec["installment"] = inst_clean or inst_text
    rec["installment_monthly"] = inst_monthly
    rating_el = card.select_one(selectors.get("rating_value") or "")
    try:  rec["rating"] = float(re.sub(r'[^\d,\.]', '', rating_el.get_text()).replace(',', '.')) if rating_el and rating_el.get_text().strip() else None
    except Exception: rec["rating"] = None

    rb = card.select_one(selectors.get("rating_block") or "")
    if rb:
        rb_text = rb.get_text(" ", strip=True)
        rec["reviews_count"] = parse_reviews_count(rb_text)
    else: rec["reviews_count"] = None

    av = card.select_one(selectors.get("availability") or "")
    rec["availability"] = av.get_text(" ", strip=True) if av else None
    disc = card.select_one(selectors.get("discount") or "")
    rec["discount"] = disc.get_text(" ", strip=True) if disc else None
    return rec