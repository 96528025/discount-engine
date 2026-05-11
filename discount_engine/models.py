from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Product:
    name: str
    price: float
    category: str = "general"

    def __post_init__(self):
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")
        if not self.name.strip():
            raise ValueError("Product name cannot be empty")


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity}")

    @property
    def subtotal(self) -> float:
        return round(self.product.price * self.quantity, 2)


@dataclass
class Coupon:
    code: str
    discount_type: str  # "percentage" or "fixed"
    value: float
    min_purchase: float = 0.0
    expiry: Optional[date] = None
    max_uses: int = -1  # -1 = unlimited
    used_count: int = 0

    def __post_init__(self):
        if self.discount_type not in ("percentage", "fixed"):
            raise ValueError(f"Invalid discount_type: {self.discount_type!r}")
        if self.value <= 0:
            raise ValueError(f"Coupon value must be positive: {self.value}")
        if self.discount_type == "percentage" and self.value > 100:
            raise ValueError(f"Percentage discount cannot exceed 100: {self.value}")

    def is_valid(self, cart_total: float) -> tuple[bool, str]:
        if self.expiry and date.today() > self.expiry:
            return False, "Coupon has expired"
        if self.max_uses != -1 and self.used_count >= self.max_uses:
            return False, "Coupon has reached maximum uses"
        if cart_total < self.min_purchase:
            return False, f"Minimum purchase of ${self.min_purchase:.2f} required"
        return True, "Valid"
