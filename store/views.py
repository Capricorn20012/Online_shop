from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from .models import Category, Product, Review,FavoriteProducts, Mail, Customer, Order, OrderProduct, ShippingAddress
from random import randint
from .forms import LoginForm, RegistrationForm, ReviewForm, CustomerForm, ShippingForm
from django.contrib.auth import login, logout
from django.contrib import messages
from shop import settings
from django.core.mail import send_mail
from .utils import CartForAuthenticatedUser, get_cart_data
import stripe

# Create your views here.

class ProductList(ListView):
    model = Product
    # context_object_name = 'categories'

    extra_context = {
        'title': 'TOTEMBO: Главная страница'
    }
    template_name = 'store/product_list.html'

    # def get_queryset(self):
    #     categories = Category.objects.filter(parent=None)
    #     return categories



class CategoryView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_page.html'  # указываем для какой страницы написана Вьюшка
    paginate_by = 1   # говорим по сколько товаров будит на странице

    def get_queryset(self):
        sort_field = self.request.GET.get('sort')  # для сортировки по цвету, материалу, цене
        type_field = self.request.GET.get('type')  # для сортировки по подкатегориям
        if type_field:   # проверка на получение кокретного продукта по ключу slug
            products = Product.objects.filter(category__slug=type_field)
            return products

        main_category = Category.objects.get(slug=self.kwargs['slug'])
        subcategories = main_category.subcategories.all()
        products = Product.objects.filter(category__in=subcategories)

        if sort_field:
            products = products.order_by(sort_field)
        return products

        # метод Динамического возврата данных
    def get_context_data(self, *, object_list=None, **kwargs):
         context = super().get_context_data()
         main_category = Category.objects.get(slug=self.kwargs['slug'])
         context['category'] = main_category
         context['title'] = f'Категория: {main_category.title}'
         return context



class ProductDetail(DetailView):  # product_detail.html
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = f'Товар: {product.title}'


        products = Product.objects.all()
        data = []
        for i in range(4):
            random_index = randint(0, len(products)-1)
            p = products[random_index]
            if p not in data:
                data.append(p)
        context['products'] = data

        context['reviews'] = Review.objects.filter(product=product)


        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForm()


        return context




def login_registration(request):
    context = {
        'title': 'Войти или Зарегистрироваться',
        'login_form': LoginForm(),
        'registration_form': RegistrationForm()
    }

    return render(request, 'store/login_registration.html', context)


def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Успешный вход в аккаунт')
        return redirect('product_list')


def user_logout(request):
    logout(request)
    messages.error(request, 'Вы вышли из аккаунта')
    return redirect('product_list')



def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Аккаунт успешно зарегистрирован')
    else:
        for field in form.errors:
            messages.error(request, form.errors[field].as_text())

    return redirect('login_registration')



def save_review(request, product_id):
    form = ReviewForm(data=request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        product = Product.objects.get(pk=product_id)
        review.product = product
        review.save()
    else:
        pass
    return redirect('product_detail', product.slug)


def save_favourite_product(request, product_slug):
    user = request.user if request.user.is_authenticated else None
    product = Product.objects.get(slug=product_slug)
    favourite_products = FavoriteProducts.objects.filter(user=user)
    if user:
        if product in [i.product for i in favourite_products]:
            fav_product = FavoriteProducts.objects.get(user=user, product=product)
            messages.warning(request, 'Продукт удалён из избранного')
            fav_product.delete()
        else:
            FavoriteProducts.objects.create(user=user, product=product)
            messages.success(request, 'Продукт успешно добавлен в Избранное')
    else:
        messages.warning(request, 'Что бы добавить в Избранное Войдите в Аккаунт или Зарегистрируйтесь')
    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


class FavouriteProductsView(LoginRequiredMixin, ListView):
    model = FavoriteProducts
    context_object_name = 'products'
    template_name = 'store/favourite_products.html'
    login_url = 'login_registration'

    def get_queryset(self):
        user = self.request.user
        favs = FavoriteProducts.objects.filter(user=user)
        products = [i.product for i in favs]
        return products


def save_email(request):
    email = request.POST.get('email')
    user = request.user if request.user.is_authenticated else None
    mail_users = Mail.objects.all()
    if user:
        if email not in [i.mail for i in mail_users]:
            Mail.objects.create(mail=email, user=user)
            messages.success(request, 'Ваша почта успешно сохранена')
        else:
            messages.warning(request, 'Ваша почта уже зарегистрированна')
    else:
        pass
    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


def send_mail_to_customer(request):
    superuser = request.user if request.user.is_superuser else None
    if superuser:
        if request.method == 'POST':
            text = request.POST.get('text')
            mail_list = Mail.objects.all()
            for email in mail_list:
                mail = send_mail(
                    subject='У нас новая акция',
                    message=text,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )
                print(f'Отправно ли сообщение на почту {email}? - {bool(mail)}')
        else:
            pass
    else:
        return redirect('product_list')

    return render(request, 'store/send_mail.html')

# ---------------------------------------------------------------------------------------------


#  Функция для страницы Корзины
def cart(request):
    if request.user.is_authenticated:
        cart_info = get_cart_data(request)
        context = {
            'cart_total_quantity': cart_info['cart_total_quantity'],
            'order': cart_info['order'],
            'products': cart_info['products']
        }

        print(context)
        return render(request, 'store/cart.html', context)
    else:
        messages.error(request, 'Авторизуйтесь или зарегистрируйтесь')
        return redirect('login_registration')


#  Функция для добавления в корзину
def to_cart(request, product_id, action):
    if request.user.is_authenticated:
        user_cart = CartForAuthenticatedUser(request, product_id, action)
        next_page = request.META.get('HTTP_REFERER', 'product_list')
        return redirect(next_page)
    else:
        messages.error(request, 'Авторизуйтесь или зарегистрируйтесь')
        return redirect('login_registration')


def checkout(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'items': cart_info['products'],

        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm(),
        'title': 'Оформление заказа'
    }

    return render(request, 'store/checkout.html', context)



def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartForAuthenticatedUser(request)
        cart_info = user_cart.get_cart_info()

        customer_form = CustomerForm(data=request.POST)
        if customer_form.is_valid():
            customer = Customer.objects.get(user=request.user)
            customer.first_name = customer_form.cleaned_data['first_name']
            customer.last_name = customer_form.cleaned_data['last_name']
            customer.save()
            user = User.objects.get(username=request.user.username)
            user.first_name = customer_form.cleaned_data['first_name']
            user.last_name = customer_form.cleaned_data['last_name']
            user.save()

        shipping_form = ShippingForm(data=request.POST)
        if shipping_form.is_valid():
            address = shipping_form.save(commit=False)
            address.customer = Customer.objects.get(user=request.user)
            address.order = user_cart.get_cart_info()['order']
            address.save()

        total_price = cart_info['cart_total_price']
        total_quantity = cart_info['cart_total_quantity']
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data':{
                        'name': 'Товара с Тотембо'
                    },
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('success'))
        )
        return redirect(session.url, 303)


def successPayment(request):
    user_cart = CartForAuthenticatedUser(request)
    user_cart.clear()
    messages.success(request, 'Оплата прошла успешно. Ожидайте заказ')
    return render(request, 'store/success.html')



























