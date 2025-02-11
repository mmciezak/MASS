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

    path('cart/remove_single/<int:item_id>/', views.remove_single_item, name='remove_single_item'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/checkout', views.checkout_view, name='checkout_view'),
    path('cart/checkout/<int:prescription_id>/', views.checkout_view, name='checkout_view_with_prescription'),

    #test
    path('check-availability/', views.check_availability, name='check_availability'),

    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-account/', views.user_account_view, name='my_account'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('products/product/<int:medication_id>/', views.product, name='product'),

    path('prescriptions/', views.prescriptions_view, name='prescriptions_view'),
    path('add-prescription/', views.add_prescription, name='add_prescription'),

    path('realize-prescription/<int:prescription_id>/', views.realize_prescription, name='realize_prescription'),

    path('manager/', views.pharmacist_view, name='manager'),
    path('doctor/', views.doctor_view, name='doctor'),

     path('symptoms/', views.symptom_advice_view, name='symptom_form'),
    #path('checkout/', checkout_view, name='checkout_view'),
    #path('checkout/<int:prescription_id>/', checkout_view, name='checkout_view_with_prescription'),

    path('write_out_prescription/', views.write_out_prescription, name='write_out_prescription'),
    path('write_out_prescription/success/', views.prescription_success, name='prescription_success'),

    path('manager/order_info/<int:order_id>', views.order_info, name='order_info'),
    path('manager/order_info/<int:order_id>/received', views.mark_as_received, name='mark_as_received'),
path('manager/order_info/<int:order_id>/ready', views.mark_as_ready, name='mark_as_ready'),
    path('manager/prescriptions', views.prescriptions_page_manager, name='prescriptions_page_manager'),
    path('place_order_for_missing_medications/', views.place_order_for_missing_medications,
    name='place_order_for_missing_medications'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
