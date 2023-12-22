from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import Sum
import decimal
from django.utils import timezone
import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='product_name')
    code = models.CharField(max_length=255, verbose_name='product_code')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    unit = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    #Элементы отображаются в порядке добавления
    class Meta:
        ordering = ['pk']
    
    #Отображение элемента в строке
    def __str__(self):
        return f'{self.name} ({self.price})'

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)

    #Элементы отображаются в порядке добавления
    class Meta:
        ordering = ['pk']

    #Отображение элемента в строке
    def __str__(self):
        return f'{self.user} ({self.amount})'
    
    #Баланс по счёту указанного пользователя
    @staticmethod
    def get_balance(user: User):
        amount = Payment.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum']
        return amount or decimal.Decimal(0)

class Order(models.Model):
    STATUS_CART = '1_cart'
    STATUS_WAITING_FOR_PAYMENT = '2_waiting_for_payment'
    STATUS_PAID = '3_paid'
    STATUS_CHOICES = (
        (STATUS_CART, 'Cart'),
        (STATUS_WAITING_FOR_PAYMENT, 'Waiting_for_payment'),
        (STATUS_PAID, 'Paid'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CART)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    
    #Элементы отображаются в порядке добавления
    class Meta:
        ordering = ['pk']
    
    #Отображение элемента в строке
    def __str__(self):
        return f'{self.user} ({self.amount}, {self.status})'
    
    #Ищем корзину, если нет, то создаём. Корзина не перешедшая в статус Заказа и старше 7 дней будет удалена
    @staticmethod
    def get_cart(user: User):
        cart = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
        if cart and timezone.now() - cart.creation_time > datetime.timedelta(days=7):
            cart.delete()
            cart = None
        if not cart:
            cart = Order.objects.create(user=user, status=Order.STATUS_CART, amount=0)
        return cart
    
    #Считаем общую сумму
    def get_amount(self):
        amount = decimal.Decimal(0)
        for item in self.orderitem_set.all():
            amount += item.amount
        return amount
    
    #Если корзина не пустая, то меняем статус на "Ожидает оплату"
    def make_order(self):
        items = self.orderitem_set.all()
        if items and self.status == Order.STATUS_CART:
            self.status = Order.STATUS_WAITING_FOR_PAYMENT
            self.save()
            auto_payment_unpaid_orders(self.user)
    
    #Смотрим общую сумму неоплаченных заказов (статус "Ожидает оплату")
    @staticmethod
    def get_amount_of_unpaid_orders(user: User):
        amount = Order.objects.filter(user=user, status=Order.STATUS_WAITING_FOR_PAYMENT).aggregate(Sum('amount'))['amount__sum']
        return amount or decimal.Decimal(0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    discount = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    #Элементы отображаются в порядке добавления
    class Meta:
        ordering = ['pk']
    
    #Отображение элемента в строке
    def __str__(self):
        return f'{self.order} ({self.product})'
    
    #Считаем сумму продукта
    @property
    def amount(self):
        return self.quantity * (self.price - self.discount)

#Автоматически оплачиваем неоплаченные заказы, если на балансе достаточно средств (меняем статус на "Оплачено", создаём антиплатеж (оплата со знаком "-")) 
@transaction.atomic()
def auto_payment_unpaid_orders(user: User):
    unpaid_orders = Order.objects.filter(user=user, status=Order.STATUS_WAITING_FOR_PAYMENT)
    for order in unpaid_orders:
        if Payment.get_balance(user) < order.amount:
            break
        order.payment = Payment.objects.all().last()
        order.status = Order.STATUS_PAID
        order.save()
        Payment.objects.create(user=user, amount=-order.amount, time=timezone.now(), comment=f'Payment for order {order}')
            
#Пересчитываем сумму в корзине после изменения (добавления) количества или цены OrderItem
@receiver(post_save, sender=OrderItem)
def recalculate_order_amount_after_save(sender, instance, **kwargs):
    order = instance.order
    order.amount = order.get_amount()
    order.save()

#Пересчитываем сумму в корзине после изменения (удаления) количества или цены OrderItem
@receiver(post_delete, sender=OrderItem)
def recalculate_order_amount_after_delete(sender, instance, **kwargs):
    order = instance.order
    order.amount = order.get_amount()
    order.save()

#Смотрим кто пополнил баланс и, если можем, совершаем автоплатеж
@receiver(post_save, sender=Payment)
def auto_payment(sender, instance, **kwargs):
    user = instance.user
    auto_payment_unpaid_orders(user)