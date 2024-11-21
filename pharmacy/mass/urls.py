from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("products/", views.products, name="products"),
    path("login/", views.login_page, name="loginPage"),
    path("register/", views.register_page, name="registerPage"),
    path('logout/', views.log_out_page, name='logOutPage'),
    path('add_to_cart/<int:medication_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/checkout', views.checkout_view, name='checkout_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
