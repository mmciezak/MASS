from datetime import datetime
import stripe
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm, CheckoutForm
from django.http import HttpResponse
from .models import Medication, Cart, CartItem, ExtendedUser, OrderItem, Order, Prescription
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
    
    # Pobierz ilość z POST i upewnij się, że jest to poprawna liczba całkowita
    try:
        quantity = int(request.POST.get('quantity', 1)) 
        if quantity <= 0:
            raise ValueError("Ilość musi być większa niż zero")
    except (ValueError, TypeError):
        # Jeśli nie uda się przekształcić na liczbę lub liczba jest <= 0, ustaw domyślną wartość 1
        quantity = 1

    extended_user, created = ExtendedUser.objects.get_or_create(user=request.user)
    
    if not extended_user.cart:
        cart = Cart.objects.create()
        extended_user.cart = cart
        extended_user.save()
    else:
        cart = extended_user.cart

    # Sprawdź, czy istnieje już element w koszyku i zaktualizuj ilość
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

def checkout_view(request, prescription_id=None):
    form = CheckoutForm()
    order = None
    user = ExtendedUser.objects.get(user=request.user)
    cart = user.cart
    cart_items = cart.items.all()
    grand_total = sum(item.quantity * item.medication.price for item in cart_items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
           
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            address = form.cleaned_data['address']
            city = form.cleaned_data['city']
            zip_code = form.cleaned_data['zip_code']
            phone = form.cleaned_data['phone']
            payment = form.cleaned_data['payment']

            # Tworzenie zamówienia
            order = Order.objects.create(
                user=user.user,
                date_of_order=datetime.now(),
                shipping_address=f"{address}, {city}, {zip_code}",
                phone_number=phone,
                payment_method=payment,
            )

            # Przeniesienie elementów z koszyka do zamówienia
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    medication=cart_item.medication,
                    quantity=cart_item.quantity,
                )

            # Obliczenie całkowitej ceny zamówienia
            order.total = order.calculate_total()
            order.save()

            # Sprawdzenie czy prescription_id zostało zapisane w sesji
            prescription_id = request.session.get('prescription_id', None)
            if prescription_id:
                prescription = get_object_or_404(Prescription, id=prescription_id)
                # Oznacz receptę jako zrealizowaną
                prescription.mark_as_realized()
                messages.success(request, "Prescription has been successfully realized.")
                # Usuwamy prescription_id z sesji
                del request.session['prescription_id']

            
            user.user_orders.add(order)
            # Czyszczenie koszyka użytkownika
            cart.items.all().delete()  # usuwa wszystkie cart item jakie byly w koszyku z bazy danych (inaczej przy nast dodaniu bedzie zla ilosc)
            cart.items.clear()

            return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {
        'form': form,
        'order': order,
        'grand_total': grand_total,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(request, 'success.html', {'order': order})

@login_required
def user_account_view(request):
    user = request.user

    try:
        extended_user = ExtendedUser.objects.get(user=user)
    except ExtendedUser.DoesNotExist:
        extended_user = None

    orders = Order.objects.filter(user=user).order_by('-date_of_order')

    context = {
        'user': user,
        'extended_user': extended_user,
        'orders': orders,
    }
    return render(request, 'my_account.html', context)


from django.contrib import messages

@login_required
def prescriptions_view(request):
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    prescriptions = extended_user.prescriptions.all()
    error = request.GET.get('error', None)

    return render(request, 'prescriptions.html', {
        'prescriptions': prescriptions,
        'error': error
    })


@login_required
def add_prescription(request):
    if request.method == "POST":
        prescription_id = request.POST.get("prescription_id")
        extended_user = get_object_or_404(ExtendedUser, user=request.user)

        try:
            prescription = Prescription.objects.get(prescription_ID=prescription_id)
            if prescription.added == False:
                extended_user.prescriptions.add(prescription)
                prescription.mark_as_added()
                extended_user.save()
                messages.success(request, "Prescription added successfully")
            else:
                messages.warning(request, "Cannot add this prescription (already added on another account)")
        except Prescription.DoesNotExist:
            messages.error(request, f"Prescription with ID {prescription_id} does not exist.")

        return redirect('prescriptions_view')
    


@login_required
def realize_prescription(request, prescription_id):
    # Pobieramy użytkownika i receptę
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    prescription = get_object_or_404(Prescription, id=prescription_id)

    # Sprawdzamy, czy recepta jest niezrealizowana
    if not prescription.realized:
        # Opróżniamy koszyk recept
        if not extended_user.prescription_cart:
            extended_user.prescription_cart = Cart.objects.create()
            extended_user.save()
        
        cart = extended_user.prescription_cart
        cart.items.clear()

        # Dodajemy produkty z recepty do koszyka
        for medication in prescription.medications.all():
            if medication.price is None:
                messages.error(request, f"Medication {medication.name} has no price set.")
                return redirect('prescriptions_view')

            cart_item, created = CartItem.objects.get_or_create(
                medication=medication, 
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()

            cart.items.add(cart_item)

        # Oznaczamy receptę jako zrealizowaną
        #prescription.mark_as_realized()

        # Przechowywanie prescription_id w sesji (?)
        request.session['prescription_id'] = prescription.id

        # Obliczamy łączną wartość koszyka
        cart_items = cart.items.all()
        grand_total = sum(item.quantity * item.medication.price for item in cart_items)

        messages.success(request, "Prescription added to cart successfully. Proceed to checkout.")
        return render(request, 'cart.html', {'cart_items': cart_items, 'grand_total': grand_total})

    else:
        # Jeśli recepta jest już zrealizowana
        messages.warning(request, "This prescription has already been realized.")
        return redirect('prescriptions_view')
