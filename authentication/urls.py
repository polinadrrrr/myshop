"""
URL configuration for myshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from authentication import views

urlpatterns = [
    path('logout/', views.logout_user, name='logout_user'),
    path('login/', views.login_user, name='login_user'),
    path('register/', views.RegisterView.as_view(), name='register'),
    # path('blog/', views.blog, name='blog'),
    # path('cart/', views.cart, name='cart'),
    # path('checkout/', views.checkout, name='checkout'),
    # path('confirmation/', views.confirmation, name='confirmation'),
    # path('contact/', views.contact, name='contact'),
    # path('elements/', views.elements, name='elements'),
    # path('login/', views.login, name='login'),
    # path('product_list/', views.product_list, name='product_list'),
    # path('register/', views.register, name='register'),
    # path('single_product/', views.single_product, name='single_product'),
    # path('single_blog/', views.single_blog, name='single_blog'),
    
    
]
