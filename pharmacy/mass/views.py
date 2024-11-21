from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm, CheckoutForm
from django.http import HttpResponse
from .models import Medication, Cart, CartItem, ExtendedUser, OrderItem, Order
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

# Widoki
def index(request):
    if request.user.is_authenticated:
        return render(request, 'index_logged_in.html')
    return render(request, 'index.html')

def products(request): 
    medications = Medication.objects.all()
    context = {"medications": medications}
    return render(request, 'products.html', context)

def login_page(request):
    form = UserCreationForm()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
    context = {"form": form}
    return render(request, 'login.html', context)

def register_page(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    context = {"form": form}
    return render(request, 'register.html', context)

def log_out_page(request):
    logout(request)
    return redirect('loginPage')

# Koszyk
@login_required
def add_to_cart(request, medication_id):
    medication = get_object_or_404(Medication, id=medication_id)
    quantity = int(request.POST.get('quantity', 1)) 
    extended_user, created = ExtendedUser.objects.get_or_create(user=request.user)
    
    if not extended_user.cart:
        cart = Cart.objects.create()
        extended_user.cart = cart
        extended_user.save()
    else:
        cart = extended_user.cart

    cart_item, created = CartItem.objects.get_or_create(medication=medication, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    cart.items.add(cart_item)

    return redirect('cart_view')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart_view')

# Widok koszyka
@login_required
def cart_view(request):
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    cart = extended_user.cart
    cart_items = cart.items.all()
    
    grand_total = sum(item.quantity * item.medication.price for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'grand_total': grand_total})

def checkout_view(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Przetwarzanie danych formularza
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            address = form.cleaned_data['address']
            city = form.cleaned_data['city']
            zip_code = form.cleaned_data['zip_code']
            phone = form.cleaned_data['phone']
            payment = form.cleaned_data['payment']

            # Tworzenie zamówienia i przypisanie do użytkownika
            user = ExtendedUser.objects.get(user=request.user)
            cart = user.cart

            order = Order.objects.create(user=user, date_ordered=datetime.now())

            for cart_item in cart.items.all():
                OrderItem.objects.create(order=order,
                                         medication=cart_item.medication,
                                         quantity=cart_item.quantity)
            order.shipping_address = f"{address}, {city}, {zip_code}"
            order.phone_number = phone

            order.save()
            user.user_orders.add(order)
            cart.items.clear()

            return redirect('payment_view')

        else:

            form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form})


#def payment_view()

#@login_required
#def user_account(request):

