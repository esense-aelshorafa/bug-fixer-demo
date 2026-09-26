import cart as cart

item1 = cart.Item("keyboard", 50.0, 2)
item2 = cart.Item("mouse", 20.0)
my_cart = cart.Cart()
my_cart.add(item1)
my_cart.add(item2)
print(my_cart.subtotal())
print(my_cart.apply_discount(90))