from django import forms
from shop.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'code', 'price', 'unit', 'image_url', 'note')
