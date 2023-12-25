from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import Sum
import decimal
from django.utils import timezone
import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ValidationError


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='product_name')
    code = models.CharField(max_length=255, verbose_name='product_code')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    unit = models.CharField(max_length=255, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    #Элементы отображаются в порядке добавления
    class Meta:
        ordering = ['pk']
    
    #Отображение элемента в строке
    def __str__(self):
        return f'{self.name} ({self.price}, {self.stock})'
    
    

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
    
    #Метод, который позволяет получить баланс по счёту указанного пользователя
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
    
    #При выборе товара пользователем, товар в выбранном количестве добавляется в корзину Cart, которая создаётся автоматически при первом вызове метода get_cart(user)
    #Корзина, не перешедшая в статус Заказа в течении 7 дней, автоматически удаляется при первом же вызове метода get_cart(user)
    @staticmethod
    def get_cart(user: User):
        cart = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
        if cart and timezone.now() - cart.creation_time > datetime.timedelta(days=7):
            cart.delete()
            cart = None
        if not cart:
            cart = Order.objects.create(user=user, status=Order.STATUS_CART, amount=0)
        return cart
    
    #Считаем общую сумму в корзине
    def get_amount(self):
        amount = decimal.Decimal(0)
        for item in self.orderitem_set.all():
            amount += item.amount
        return amount
    
    #После завершения набора/изменения Корзины и перехода к оплате, Корзина меняет статус (если она не пустая!) и становиться Заказом, ожидающим оплаты (waiting_for_payment)
    def make_order(self):
        items = self.orderitem_set.all()
        if items and self.status == Order.STATUS_CART:
            self.status = Order.STATUS_WAITING_FOR_PAYMENT
            self.save()
            auto_payment_unpaid_orders(self.user)
    
    #Метод, который позволяет получить общую сумму неоплаченных заказов (status=waiting_for_payment) по указанному пользователю
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

    #Считаем сумму товара
    @property
    def amount(self):
        if self.discount > 0 and self.price > self.discount:
            return self.quantity * (self.price - self.discount)
        return self.quantity * self.price


#Смена статуса на waiting_for_payment автоматически запускает проверку баланса текущего пользователя. 
#Если сумма баланса >= сумме заказа, то Заказ изменяет свой статус на оплаченный. 
#При этом параллельно создаётся оплата, равная (минус) сумме заказа, что сразу же после оплаты уменьшает баланс счёта клиента на сумму заказа
#Если внесённой суммы оплаты достаточно для оплаты нескольких заказов, ожидающих оплаты, то все эти заказы изменяют свой статус на оплаченный.
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
            
#При каждом новом добавлении (удалении, изменении) количества (или цены) товара, общая сумма заказа автоматически пересчитывается
@receiver(post_save, sender=OrderItem)
def recalculate_order_amount_after_save(sender, instance, **kwargs):
    order = instance.order
    order.amount = order.get_amount()
    order.save()

@receiver(post_delete, sender=OrderItem)
def recalculate_order_amount_after_delete(sender, instance, **kwargs):
    order = instance.order
    order.amount = order.get_amount()
    order.save()

#При каждом добавлении (удалении, изменении) количества товара, остаток на складе уменьшается/увеличивается
@receiver(post_save, sender=OrderItem)
def update_stock_after_save(sender, instance, **kwargs):
    instance.product.stock -= instance.quantity
    instance.product.save()

@receiver(post_delete, sender=OrderItem)
def update_stock_after_delete(sender, instance, **kwargs):
    instance.product.stock += instance.quantity
    instance.product.save()

#Внесение оплаты автоматически запускает механизм проверки всех неоплаченных заказов, начиная с самого старого. 
@receiver(post_save, sender=Payment)
def auto_payment(sender, instance, **kwargs):
    user = instance.user
    auto_payment_unpaid_orders(user)