from dataclasses import dataclass, field
from typing import List

from .models import CartItem
from .rules import DiscountRule


@dataclass
class DiscountBreakdown:
    rule_name: str
    discount_amount: float


@dataclass
class CheckoutResult:
    subtotal: float
    discounts: List[DiscountBreakdown]
    total_discount: float
    final_price: float
    savings_percentage: float


class DiscountEngine:
    """将折扣规则应用到购物车，返回最终结算结果"""

    def __init__(self, stackable: bool = True):
        self.rules: List[DiscountRule] = []
        # stackable=True：叠加所有规则；False：只取最优单一规则
        self.stackable = stackable

    def add_rule(self, rule: DiscountRule) -> "DiscountEngine":
        self.rules.append(rule)
        return self  # 支持链式调用

    def checkout(self, items: List[CartItem]) -> CheckoutResult:
        if not items:
            raise ValueError("Cannot checkout with empty cart")

        subtotal = round(sum(item.subtotal for item in items), 2)

        if self.stackable:
            return self._apply_stackable(items, subtotal)
        return self._apply_best_only(items, subtotal)

    def _apply_stackable(self, items: List[CartItem], subtotal: float) -> CheckoutResult:
        breakdowns = []
        remaining = subtotal

        for rule in self.rules:
            discount = rule.apply(items, remaining)
            if discount > 0:
                breakdowns.append(DiscountBreakdown(rule.description(), discount))
                remaining = round(remaining - discount, 2)

        total_discount = round(subtotal - remaining, 2)
        savings_pct = round(total_discount / subtotal * 100, 2) if subtotal > 0 else 0.0

        return CheckoutResult(
            subtotal=subtotal,
            discounts=breakdowns,
            total_discount=total_discount,
            final_price=remaining,
            savings_percentage=savings_pct,
        )

    def _apply_best_only(self, items: List[CartItem], subtotal: float) -> CheckoutResult:
        best_rule = None
        best_discount = 0.0

        for rule in self.rules:
            discount = rule.apply(items, subtotal)
            if discount > best_discount:
                best_discount = discount
                best_rule = rule

        breakdowns = []
        if best_rule and best_discount > 0:
            breakdowns.append(DiscountBreakdown(best_rule.description(), best_discount))

        final_price = round(subtotal - best_discount, 2)
        savings_pct = round(best_discount / subtotal * 100, 2) if subtotal > 0 else 0.0

        return CheckoutResult(
            subtotal=subtotal,
            discounts=breakdowns,
            total_discount=best_discount,
            final_price=final_price,
            savings_percentage=savings_pct,
        )
