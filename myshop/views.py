from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def blog(request):
    return render(request, 'blog.html')

def cart(request):
    return render(request, 'cart.html')

def checkout(request):
    return render(request, 'checkout.html')

def confirmation(request):
    return render(request, 'confirmation.html')

def contact(request):
    return render(request, 'contact.html')

def elements(request):
    return render(request, 'elements.html')

def login(request):
    return render(request, 'login.html')

def product_list(request):
    return render(request, 'product_list.html')

def register(request):
    return render(request, 'register.html')

def single_product(request):
    return render(request, 'single-product.html')

def single_blog(request):
    return render(request, 'single-blog.html')
