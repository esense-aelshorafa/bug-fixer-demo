"""A tiny shopping-cart module used as the demo target for the Bug Fixer agent."""
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1


@dataclass
class Cart:
    items: list[Item] = field(default_factory=list)

    def add(self, item: Item) -> None:
        self.items.append(item)

    def subtotal(self) -> float:
        return round(sum(i.price * i.quantity for i in self.items), 2)

    def apply_discount(self, percent: float) -> float:
        """Return the total after a percentage discount.

        `percent` is on a 0-100 scale, e.g. 10 means 10% off.
        """
        return round(self.subtotal() * (1 - percent), 2)
