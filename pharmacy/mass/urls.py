from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("products/", views.products, name="products"),
    path("login/", views.loginPage, name="loginPage"),
    path("register/", views.registerPage, name="registerPage"),
    path('logout/', views.logOutPage, name='logOutPage'),
    path('add_to_cart/<int:medication_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
