from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

from src.utils import parse_smartphone_title_improved

def parse_price_to_int(price_text: Optional[str]) -> Optional[int]:
    if not price_text: return None
    s = re.sub(r'[^\d]', '', price_text)
    return int(s) if s else None

def safe_text(el) -> Optional[str]:
    if el is None: return None
    try: return el.get_text(" ", strip=True)
    except Exception:
        try: return str(el)
        except Exception: return None

@dataclass
class Product:
    product_url: Optional[str] = None
    product_guid: Optional[str] = None
    product_code: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    price: Optional[int] = None
    old_price: Optional[int] = None
    installment_price: Optional[str] = None
    installment_monthly: Optional[int] = None
    diagonal_in: Optional[float] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    battery_mah: Optional[int] = None
    camera_list_mp: List[int] = field(default_factory=list)
    num_cameras: Optional[int] = None
    max_camera_mp: Optional[int] = None
    screen_type: Optional[str] = None
    resolution: Optional[str] = None
    has_nfc: Optional[bool] = None
    has_5g: Optional[bool] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    availability: Optional[str] = None
    discount: Optional[str] = None
    specs_raw: Optional[str] = None
    img_url: Optional[str] = None
    price_segment: Optional[str] = None
    value_score: Optional[float] = None
    value_category: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_title(cls, title: str, product_url: str = "") -> "Product":
        parsed = parse_smartphone_title_improved(title or "")
        product = cls(
            product_url=product_url,
            diagonal_in=parsed.get("diagonal_in"),
            brand=parsed.get("brand"),
            model=parsed.get("model"),
            storage_gb=parsed.get("storage_gb"),
            color=parsed.get("color"),
            ram_gb=parsed.get("ram_gb"),
            battery_mah=parsed.get("battery_mah"),
            screen_type=parsed.get("screen_type"),
            resolution=parsed.get("resolution"),
            camera_list_mp=parsed.get("camera_list_mp") or [],
            num_cameras=parsed.get("num_cameras"),
            max_camera_mp=parsed.get("max_camera_mp"),
            has_nfc=bool(parsed.get("has_nfc")),
            has_5g=bool(parsed.get("has_5g")),
            specs_raw=parsed.get("specs_raw"),
        )
        product.calculate_targets()
        return product

    @classmethod
    def from_catalog_record(cls, rec: Dict[str, Any]) -> "Product":
        title = rec.get("title_raw") or ""
        product = cls.from_title(title, product_url=rec.get("product_url") or "")
        product.product_guid = rec.get("product_guid") or product.product_guid
        product.product_code = rec.get("product_code") or product.product_code
        product.price = rec.get("price") or product.price
        product.old_price = rec.get("old_price") or product.old_price
        product.installment_price = rec.get("installment") or product.installment_price
        try: product.installment_monthly = int(rec.get("installment_monthly")) if rec.get("installment_monthly") is not None else product.installment_monthly
        except Exception: product.installment_monthly = product.installment_monthly

        try:
            rv = rec.get("rating")
            if rv is not None: product.rating = float(rv)
        except Exception: product.rating = product.rating

        try:
            rc = rec.get("reviews_count")
            if rc is not None:
                if isinstance(rc, (int, float)): product.reviews_count = int(rc)
                else:
                    s = re.sub(r'[^\d]', '', str(rc))
                    product.reviews_count = int(s) if s else None
        except Exception: pass

        product.availability = rec.get("availability") or product.availability
        product.discount = rec.get("discount") or product.discount
        product.img_url = rec.get("img_url") or product.img_url
        product.extra["catalog_raw"] = rec

        if product.camera_list_mp and isinstance(product.camera_list_mp, str):
            nums = re.findall(r'(\d{1,3})', product.camera_list_mp)
            product.camera_list_mp = [int(x) for x in nums] if nums else []
        if product.camera_list_mp:
            product.num_cameras = len(product.camera_list_mp)
            product.max_camera_mp = max(product.camera_list_mp)

        product.calculate_targets()
        return product

    def calculate_targets(self):
        self._calculate_price_segment()
        self._calculate_value_score()

    def _calculate_price_segment(self):
        if not self.price:
            self.price_segment = None
            return

        if self.price < 10000: self.price_segment = "budget"
        elif self.price < 20000: self.price_segment = "mid-range"
        elif self.price < 40000: self.price_segment = "premium"
        else: self.price_segment = "flagship"

    def _calculate_value_score(self):
        if not self.price or self.price <= 0:
            self.value_score = None
            self.value_category = None
            return

        rating_factor = 0.5
        discount_factor = 1.0
        feature_score = 0
        if self.ram_gb:
            feature_score += self.ram_gb * 1000
        if self.storage_gb:
            feature_score += self.storage_gb * 50
        if self.max_camera_mp:
            feature_score += self.max_camera_mp * 100
        if self.has_5g:
            feature_score += 1000
        if self.old_price and self.old_price > self.price:
            discount_factor = 1 + (self.old_price - self.price) / self.old_price
        if self.rating:
            rating_factor = max(0, min(1, (self.rating - 3) / 2))

        value_score = discount_factor * (feature_score / self.price) * rating_factor
        self.value_score = round(value_score, 3)

        if self.value_score >= 0.3: self.value_category = "exceptional_value"
        elif self.value_score >= 0.2: self.value_category = "great_value"
        elif self.value_score >= 0.1:  self.value_category = "good_value"
        elif self.value_score >= 0.05: self.value_category = "average_value"
        else: self.value_category = "poor_value"

    def to_record(self) -> Dict[str, Any]:
        record = {"product_url": self.product_url,
            "product_guid": self.product_guid,
            "product_code": self.product_code,
            "brand": self.brand,
            "model": self.model,
            "color": self.color,
            "price": self.price,
            "old_price": self.old_price,
            "installment_price": self.installment_price,
            "installment_monthly": self.installment_monthly,
            "diagonal_in": self.diagonal_in,
            "ram_gb": self.ram_gb,
            "storage_gb": self.storage_gb,
            "battery_mah": self.battery_mah,
            "num_cameras": self.num_cameras,
            "max_camera_mp": self.max_camera_mp,
            "camera_list_mp": ",".join(map(str, self.camera_list_mp)) if self.camera_list_mp else None,
            "screen_type": self.screen_type,
            "resolution": self.resolution,
            "has_nfc": int(bool(self.has_nfc)) if self.has_nfc is not None else None,
            "has_5g": int(bool(self.has_5g)) if self.has_5g is not None else None,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "availability": self.availability,
            "discount": self.discount,
            "img_url": self.img_url,
            "specs_raw": self.specs_raw,
            "price_segment": self.price_segment,
            "value_score": self.value_score,
            "value_category": self.value_category}

        record.update(self.extra)
        return record

    def __repr__(self):
        return f"Product({self.brand} {self.model}, price: {self.price}, segment: {self.price_segment}, value: {self.value_score})"