from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def cart(request):
    return render(request, 'cart.html')

def contact(request):
    return render(request, 'contact.html')

def login(request):
    return render(request, 'login.html')

def product_list(request):
    return render(request, 'product_list.html')

def register(request):
    return render(request, 'register.html')

def single_product(request):
    return render(request, 'single_product.html')
