## Summary
Applying a percentage discount to a cart returns a negative total.

## Steps to reproduce
```python
from shop.cart import Cart, Item

cart = Cart()
cart.add(Item("keyboard", 100.0, 2))
print(cart.apply_discount(10))
```

## Expected
`180.0` (subtotal is 200.00, minus 10%)

## Actual
`-1800.0`

## Environment
Python 3.12, shop 0.1.0
