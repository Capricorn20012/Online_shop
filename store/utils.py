from .models import Product, OrderProduct, Order, Customer

# Класс который будит отвечать за всю корзину, создавать и возвращать данные
class CartForAuthenticatedUser:
    def __init__(self, request, product_id=None, action=None):
        self.user = request.user

        if product_id and action:
            self.add_or_delete(product_id, action)




    # Метод который будит возвращать информацию о корзине
    def get_cart_info(self):
        customer, created = Customer.objects.get_or_create(user=self.user)  # Если есть покупатель получить, если нет то создать

        order, created = Order.objects.get_or_create(customer=customer)  # Если есть заказ получить, если нет то создать
        order_products = order.orderproduct_set.all()  # получаем все продукты заказа

        cart_total_quantity = order.get_cart_total_quantity
        cart_total_price = order.get_cart_total_price


        return {
            'cart_total_quantity': cart_total_quantity,
            'cart_total_price': cart_total_price,
            'products': order_products,
            'order': order
        }

    def add_or_delete(self, product_id, action):
        order = self.get_cart_info()['order']  # Получаем заказ
        product = Product.objects.get(pk=product_id)  # получаем продукт
        order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)

        if action == 'add' and product.quantity > 0:
            order_product.quantity += 1
            product.quantity -= 1
        else:
            order_product.quantity -= 1
            product.quantity += 1
        product.save()
        order_product.save()

        if order_product.quantity <= 0:
            order_product.delete()


    def clear(self):
        order = self.get_cart_info()['order']  # Получаем заказ
        order_products = order.orderproduct_set.all()
        for product in order_products:
            product.delete()
        order.save()




def get_cart_data(request):

    cart = CartForAuthenticatedUser(request)
    cart_info = cart.get_cart_info()

    return {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'cart_total_price': cart_info['cart_total_price'],
        'order': cart_info['order'],
        'products': cart_info['products']
    }




