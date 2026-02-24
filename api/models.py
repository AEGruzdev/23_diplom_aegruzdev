from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class Shop(models.Model):
    """Модель магазина/поставщика"""
    name = models.CharField(max_length=100, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь-владелец',
        null=True, 
        blank=True,
        related_name='shop'
    )
    state = models.BooleanField(default=True, verbose_name='Статус приема заказов')
    
    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Модель категории товаров"""
    name = models.CharField(max_length=100, verbose_name='Название')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель товара"""
    name = models.CharField(max_length=200, verbose_name='Название')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория',
                                related_name='products')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """Модель информации о товаре в конкретном магазине"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар',
                               related_name='product_infos')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин',
                            related_name='product_infos')
    name = models.CharField(max_length=200, verbose_name='Название')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Рекомендуемая цена')
    
    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товарах'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_shop')
        ]

    def __str__(self):
        return f"{self.product.name} - {self.shop.name}"


class Parameter(models.Model):
    """Модель параметра товара"""
    name = models.CharField(max_length=50, verbose_name='Название')
    
    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """Модель значения параметра товара"""
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                    related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, verbose_name='Параметр',
                                 related_name='product_parameters')
    value = models.CharField(max_length=100, verbose_name='Значение')
    
    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = 'Параметры товаров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]

    def __str__(self):
        return f"{self.product_info.product.name} - {self.parameter.name}: {self.value}"


class Contact(models.Model):
    """Модель контактов пользователя"""
    CONTACT_TYPES = [
        ('email', 'Email'),
        ('phone', 'Телефон'),
        ('address', 'Адрес'),
    ]
    
    type = models.CharField(max_length=20, choices=CONTACT_TYPES, verbose_name='Тип')
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        related_name='contacts'
    )
    value = models.CharField(max_length=200, verbose_name='Значение')
    
    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()}: {self.value}"


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = [
        ('basket', 'Корзина'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Покупатель',
        related_name='orders'
    )
    dt = models.DateTimeField(default=timezone.now, verbose_name='Дата и время')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='basket', 
                            verbose_name='Статус')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='Контакт', related_name='orders')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-dt']

    def __str__(self):
        return f"Заказ №{self.id} от {self.user.username}"


class OrderItem(models.Model):
    """Модель позиции заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ',
                             related_name='items')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, 
                                    verbose_name='Информация о товаре')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин')
    quantity = models.PositiveIntegerField(verbose_name='Количество', 
                                          validators=[MinValueValidator(1)])
    
    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item')
        ]

    def __str__(self):
        return f"{self.product_info.product.name} - {self.quantity} шт."