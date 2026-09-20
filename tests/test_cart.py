from shop.cart import Cart, Item


def test_subtotal_multiplies_price_by_quantity():
    cart = Cart()
    cart.add(Item("keyboard", 50.0, 2))
    cart.add(Item("mouse", 20.0))
    assert cart.subtotal() == 120.0


def test_empty_cart_subtotal_is_zero():
    assert Cart().subtotal() == 0


def test_zero_percent_discount_keeps_total():
    cart = Cart()
    cart.add(Item("book", 30.0))
    assert cart.apply_discount(0) == 30.0
