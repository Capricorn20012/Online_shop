from django import template
from store.models import Category, FavoriteProducts

register = template.Library()


@register.simple_tag()
def get_categories():  # Функция для получения глав категории
    return Category.objects.filter(parent=None)  # у которой нет родителя


@register.simple_tag()
def get_subcategories(category):  # В данную функция отпрю глав категорию родителя
    return Category.objects.filter(parent=category)  # получем подкатегории опредю родителя(категории)

@register.simple_tag()
def get_sorted():
    sorters =[
        {
            'title': 'По цене',
            'sorters': [
                ('price', 'По возрастанию'),
                ('-price', 'По убыванию')
            ]
        },
        {
            'title': 'По цвету',
            'sorters': [
                ('color', 'От А до Я'),
                ('-color', 'От Я до А')
            ]
        },
        {
            'title': 'По размеру',
            'sorters': [
                ('size', 'По возрастанию'),
                ('-size', 'По убыванию')
            ]
        }
    ]
    return sorters


@register.simple_tag()
def get_favourite_products(user):
    fav = FavoriteProducts.objects.filter(user=user)
    products = [i.product for i in fav]
    return products
