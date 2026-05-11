from abc import ABC, abstractmethod
from typing import List

from .models import CartItem, Coupon


class DiscountRule(ABC):
    @abstractmethod
    def apply(self, items: List[CartItem], subtotal: float) -> float:
        """返回折扣金额（正数）"""

    @abstractmethod
    def description(self) -> str:
        pass


class PercentageDiscount(DiscountRule):
    """百分比折扣，如打九折 = PercentageDiscount(10)"""

    def __init__(self, percentage: float):
        if not 0 < percentage <= 100:
            raise ValueError(f"Percentage must be between 0 and 100: {percentage}")
        self.percentage = percentage

    def apply(self, items: List[CartItem], subtotal: float) -> float:
        return round(subtotal * self.percentage / 100, 2)

    def description(self) -> str:
        return f"{self.percentage}% off"


class FixedDiscount(DiscountRule):
    """固定金额折扣，如直减20元"""

    def __init__(self, amount: float):
        if amount <= 0:
            raise ValueError(f"Fixed discount amount must be positive: {amount}")
        self.amount = amount

    def apply(self, items: List[CartItem], subtotal: float) -> float:
        # 折扣不会超过小计，避免负数
        return round(min(self.amount, subtotal), 2)

    def description(self) -> str:
        return f"${self.amount:.2f} off"


class ThresholdDiscount(DiscountRule):
    """满减：满 threshold 减 discount_amount"""

    def __init__(self, threshold: float, discount_amount: float):
        if threshold <= 0:
            raise ValueError(f"Threshold must be positive: {threshold}")
        if discount_amount <= 0:
            raise ValueError(f"Discount amount must be positive: {discount_amount}")
        self.threshold = threshold
        self.discount_amount = discount_amount

    def apply(self, items: List[CartItem], subtotal: float) -> float:
        if subtotal >= self.threshold:
            return round(min(self.discount_amount, subtotal), 2)
        return 0.0

    def description(self) -> str:
        return f"${self.discount_amount:.2f} off orders over ${self.threshold:.2f}"


class BuyXGetYDiscount(DiscountRule):
    """买X送Y：最便宜的Y件免费"""

    def __init__(self, buy: int, get: int):
        if buy <= 0 or get <= 0:
            raise ValueError("Buy and get quantities must be positive")
        self.buy = buy
        self.get = get

    def apply(self, items: List[CartItem], subtotal: float) -> float:
        # 展开所有单件价格
        all_prices = []
        for item in items:
            all_prices.extend([item.product.price] * item.quantity)

        group_size = self.buy + self.get
        if len(all_prices) < group_size:
            return 0.0

        # 升序排列，最便宜的免费
        all_prices.sort()

        discount = 0.0
        i = 0
        while i + group_size <= len(all_prices):
            for j in range(self.get):
                discount += all_prices[i + j]
            i += group_size

        return round(discount, 2)

    def description(self) -> str:
        return f"Buy {self.buy} get {self.get} free"


class CouponDiscount(DiscountRule):
    """优惠券折扣"""

    def __init__(self, coupon: Coupon):
        self.coupon = coupon

    def apply(self, items: List[CartItem], subtotal: float) -> float:
        valid, _ = self.coupon.is_valid(subtotal)
        if not valid:
            return 0.0
        if self.coupon.discount_type == "percentage":
            return round(subtotal * self.coupon.value / 100, 2)
        return round(min(self.coupon.value, subtotal), 2)

    def description(self) -> str:
        return f"Coupon {self.coupon.code}"
