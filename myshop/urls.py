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
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('auth/', include('authentication.urls')),
    path('shop/', include('shop.urls')),
    
    path('about/', views.about, name='about'),
    #path('cart/', views.cart, name='cart'),
    path('catalog/', views.catalog, name='catalog'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    #
    #path('product_list/', views.product_list, name='product_list'),
    #
    #path('single_product/', views.single_product, name='single_product'),
]
