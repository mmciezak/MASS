from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .views import filter_list

urlpatterns = [
    path("", views.index, name="index"),
    path("products/", filter_list, name="products"),
    path("login/", views.login_page, name="loginPage"),
    path("register/", views.register_page, name="registerPage"),
    path('logout/', views.log_out_page, name='logOutPage'),
    path('add_to_cart/<int:medication_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('cart/', views.cart_view, name='cart_view'),
    path('cart/checkout', views.checkout_view, name='checkout_view'),
    path('cart/checkout/<int:prescription_id>/', views.checkout_view, name='checkout_view_with_prescription'),

    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-account/', views.user_account_view, name='my_account'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('prescriptions/', views.prescriptions_view, name='prescriptions_view'),
    path('add-prescription/', views.add_prescription, name='add_prescription'),

    path('realize-prescription/<int:prescription_id>/', views.realize_prescription, name='realize_prescription'),

    #path('checkout/', checkout_view, name='checkout_view'),
    #path('checkout/<int:prescription_id>/', checkout_view, name='checkout_view_with_prescription'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
