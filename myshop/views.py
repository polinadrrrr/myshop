from django.shortcuts import get_object_or_404, redirect, render

from shop.models import Product
from .forms import ProductForm

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def cart(request):
    return render(request, 'cart.html')

def catalog(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('catalog')
    else:
        form = ProductForm()
    return render(request, 'catalog.html', {'form': form})

def product_edit(request, pk):
    post = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=post)
    return render(request, 'catalog.html', {'form': form})

def login(request):
    return render(request, 'login.html')

def product_list(request):
    return render(request, 'product_list.html')

def register(request):
    return render(request, 'register.html')

def single_product(request):
    return render(request, 'single_product.html')
