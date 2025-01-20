from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm, CheckoutForm
from .models import Medication, Cart, CartItem, ExtendedUser, OrderItem, Order, Prescription, Location, MedicationStock, \
    PharmacyOrder, PharmacyOrderItem
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .forms import SymptomForm
import re
import unidecode

# Widoki
def index(request):
    if request.user.is_authenticated:
        return render(request, 'index_logged_in.html')
    return render(request, 'index.html')

def products(request): 
    medications = Medication.objects.all()
    context = {"medications": medications}
    return render(request, 'products.html', context)

def product(request, medication_id): 
    medication = get_object_or_404(Medication, id=medication_id)
    return render(request, 'product.html', {'medication': medication})
    

def filter_list(request):
    category = request.GET.get('category')
    search = request.GET.get('search')

    medications = Medication.objects.all()
    if category:
        medications = medications.filter(category_tag=category)
    if search:
        medications = medications.filter(name__icontains=search) | medications.filter(description__icontains=search)


    categories = Medication.Category.choices
    return render(request, 'products.html', {'medications' : medications, 'categories': categories})

def login_page(request):
    form = UserCreationForm()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if hasattr(request.user, 'extendeduser') and request.user.extendeduser.is_manager:
                return redirect('manager')
            elif hasattr(request.user, 'extendeduser') and request.user.extendeduser.is_doctor:
                return redirect('doctor')
            else:
                return redirect('index')
        else:
            messages.error(request, "Niepoprawna nazwa użytkownika lub hasło.")
            return redirect('loginPage')
    context = {"form": form}
    return render(request, 'login.html', context)

def register_page(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # stworzenie koszyka
            extended_user = ExtendedUser.objects.create(
                user=user,
                cart=Cart.objects.create(),
                prescription_cart=Cart.objects.create()  # opcjonalne, jeśli potrzebny koszyk na recepty
            )

            login(request, user)  
            return redirect('index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
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

    # Sprawdź, czy istnieje już CartItem z tą samą instancją `medication` w tym koszyku
    existing_cart_item = cart.items.filter(medication=medication).first()
    
    if existing_cart_item:
        # Jeśli istnieje, dodaj ilość
        existing_cart_item.quantity += quantity
        existing_cart_item.save()
    else:
        # Jeśli nie istnieje, utwórz nowy `CartItem` i dodaj go do koszyka
        cart_item = CartItem.objects.create(medication=medication, quantity=quantity)
        cart.items.add(cart_item)

    return redirect('cart_view')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    cart_item.delete()

    return redirect('cart_view')

@login_required
def remove_single_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if cart_item.quantity > 1:
        # Zmniejszenie ilości o 1
        cart_item.quantity -= 1
        cart_item.save()
    else:
        # Usunięcie, jeśli to ostatnia sztuka
        cart_item.delete()

    return redirect('cart_view')  # Przekierowanie na stronę koszyka

# Widok koszyka
@login_required
def cart_view(request):
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    cart = extended_user.cart
    cart_items = cart.items.all()
    request.session['prescription_id'] = None
    grand_total = sum(item.quantity * item.medication.price for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'grand_total': grand_total})

def checkout_view(request, prescription_id=None):
    prescription_id = request.session.get('prescription_id', None)
    locations = Location.objects.all()
    form = CheckoutForm()
    order = None
    user = ExtendedUser.objects.get(user=request.user)
    if prescription_id:
        cart = user.prescription_cart
    else:
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
            location = form.cleaned_data['location']

            # Tworzenie zamówienia
            order = Order.objects.create(
                user=user.user,
                date_of_order=datetime.now(),
                shipping_address=f"{address}, {city}, {zip_code}",
                phone_number=phone,
                location=Location.objects.get(address=location),
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

                # Sprawdzenie dostępności leków w magazynie
            unavailable_items = []
            for cart_item in cart_items:
                stock = MedicationStock.objects.filter(location=location,
                                                        medication=cart_item.medication).first()
                if not stock or stock.quantity < cart_item.quantity:
                    unavailable_items.append(cart_item.medication.name)
                    report_missing_medication(location, cart_item.medication, cart_item.quantity)

            user.user_orders.add(order)
            # Czyszczenie koszyka użytkownika
            cart.items.all().delete()  # usuwa wszystkie cart item jakie byly w koszyku z bazy danych (inaczej przy nast dodaniu bedzie zla ilosc)
            cart.items.clear()

            return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {
        'form': form,
        'order': order,
        'grand_total': grand_total,
        'cart_items': cart_items,
        'locations': locations,  # Przekazanie listy aptek
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
                messages.success(request, "Recepta została dodana pomyślnie")
            else:
                messages.warning(request, "Recepta już została dodana.")
        except Prescription.DoesNotExist:
            messages.error(request, f"Recepta o takim ID: {prescription_id} nie istnieje.")

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
        cart.items.all().delete()  # usuwa wszystkie cart item jakie byly w koszyku z bazy danych
        cart.items.clear()

        # Dodajemy produkty z recepty do koszyka
        for index, medication in enumerate(prescription.medications.all()):#pobieramy indeks leku i lek

            quantity = 1
            if prescription.quantities:
                quantity = prescription.quantities[index]

            if medication.price is None:
                messages.error(request, f"Medication {medication.name} has no price set.")
                return redirect('prescriptions_view')

            # Tworzymy nowy CartItem za każdym razem
            cart_item = CartItem.objects.create(
                medication=medication,
                quantity=quantity
            )
            cart.items.add(cart_item)

        # Oznaczamy receptę jako zrealizowaną
        # prescription.mark_as_realized()

        # Przechowywanie prescription_id w sesji (?)
        request.session['prescription_id'] = prescription.id

        # Obliczamy łączną wartość koszyka
        cart_items = cart.items.all()
        grand_total = sum(item.quantity * item.medication.price for item in cart_items)
        #cart.items.all().delete()  # usuwa wszystkie cart item jakie byly w koszyku z bazy danych
        #cart.items.clear()

        messages.success(request, "Recepta dodana do koszyka. Przejdź do podsumowania.")
        return render(request, 'cart.html', {'cart_items': cart_items, 'grand_total': grand_total})

    else:
        # Jeśli recepta jest już zrealizowana
        messages.warning(request, "Ta recepta już została zrealizowana.")
        return redirect('prescriptions_view')

def is_manager(user):
    return user.is_authenticated and hasattr(user, 'extendeduser') and user.extendeduser.is_manager

def is_doctor(user):
    return user.is_authenticated and hasattr(user, 'extendeduser') and user.extendeduser.is_doctor



@user_passes_test(is_doctor)
def doctor_view(request):
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    user_location = extended_user.location  # Lokalizacja apteki

    # Pobieramy wszystkie zamówienia z lokalizacji apteki
    all_orders = Order.objects.filter(location=user_location).order_by('-date_of_order')

    # Pobieramy wszystkie leki dostępne w systemie
    all_medications = Medication.objects.all()

    # Pobieramy wszystkie recepty w systemie
    #all_prescriptions = Prescription.objects.all()

    # Obsługa wyszukiwania recept
    #search_query = request.GET.get('search', None)
    #searched_prescriptions = None
    #if search_query:
    #    searched_prescriptions = Prescription.objects.filter(
    #        prescription_ID=search_query
    #    )

    return render(request, 'doctor.html', {
        #'all_orders': all_orders,
        #'all_prescriptions': all_prescriptions,
        'medications': all_medications,  # Przekazujemy wszystkie leki w systemie
        #'searched_prescriptions': searched_prescriptions,
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import Medication, Prescription
from django.utils.timezone import now
import json

@user_passes_test(is_doctor)
def write_out_prescription(request):
    if request.method == "POST":
        # Extract POST data
        prescription_ID = request.POST.get("prescription_ID")
        patient_name = request.POST.get("patient_name")
        date_prescribed = request.POST.get("date_prescribed", now().date())
        medications_ids = request.POST.getlist("medications")
        quantities = request.POST.getlist("quantities")
        realized = request.POST.get("realized") == "on"
        added = request.POST.get("added") == "on"

        # Check if the prescription already exists
        if Prescription.objects.filter(prescription_ID=prescription_ID).exists():
            messages.error(request, "Recepta o podanym ID już istnieje.")
            # Re-render the form with an error message
            medications = Medication.objects.all()
            context = {
                "medications": medications,
                "today": now().date(),
                "patient_name": patient_name,
                "prescription_ID": prescription_ID,
                "realized": realized,
                "added": added,
            }
            return render(request, 'add_prescription.html', context)

        # Create and save the prescription
        prescription = Prescription(
            prescription_ID=prescription_ID,
            patient_name=patient_name,
            date_prescribed=date_prescribed,
            realized=realized,
            added=added,
        )
        prescription.save()

        # Set medications and quantities
        medications = Medication.objects.filter(id__in=medications_ids)
        prescription.medications.set(medications)

        try:
            # Convert quantities to integers and save
            quantities = [int(qty) for qty in quantities]
            prescription.quantities = quantities
            prescription.save()
        except ValueError:
            messages.error(request, "Podano nieprawidłową ilość leków.")
            medications = Medication.objects.all()
            context = {
                "medications": medications,
                "today": now().date(),
                "patient_name": patient_name,
                "prescription_ID": prescription_ID,
                "realized": realized,
                "added": added,
            }
            return render(request, 'add_prescription.html', context)

        return redirect("/write_out_prescription/success/")

    prescription_ID = Prescription.generate_id()
    medications = Medication.objects.all()
    context = {
        "medications": medications,
        "today": now().date(),
        "prescription_ID": prescription_ID,
    }
    return render(request, 'add_prescription.html', context)

@user_passes_test(is_doctor)
def prescription_success(request):
    return render(request, 'success_prescription.html', {
        "message": "Recepta została pomyślnie zapisana."
    })


@user_passes_test(is_manager)
def order_info(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_info.html', {'order' : order})

@user_passes_test(is_manager)
def mark_as_received(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Flag to track if there is enough stock for all items in the order
    is_in_stock = True

    # Loop through each order item and check if stock is sufficient
    for item in order.order_items.all():
        stock = MedicationStock.objects.filter(location=order.location, medication=item.medication).first()
        if stock and stock.quantity < item.quantity:
            # If there is not enough stock, mark as insufficient and break
            is_in_stock = False
            break

    if not is_in_stock:
        # Add an error message if stock is insufficient for any item
        #messages.error(request, "Nie ma wystarczającej ilości towaru w magazynie, aby oznaczyć zamówienie jako otrzymane.")
        return redirect('order_info', order_id=order.id)

    # If there is sufficient stock, proceed with marking the order as received
    if order.status != Order.Status.EXPIRED:
        order.receive_order()
        order.save()

        # Decrease the quantity of medications in the stock
        for item in order.order_items.all():
            # Fetch the stock for this medication at the order's location
            stock = MedicationStock.objects.filter(location=order.location, medication=item.medication).first()

            if stock:
                # Decrease the stock by the order's quantity
                delete_from_stock(order.location, item.medication, item.quantity)

    return redirect('order_info', order_id=order.id)


@user_passes_test(is_manager)
def prescriptions_page_manager(request):
    search_query = request.GET.get('search', '')
    searched_prescriptions = []
    if search_query:
        searched_prescriptions = Prescription.objects.filter(prescription_ID__icontains=search_query)

    all_prescriptions = Prescription.objects.all()
    context = {
        'searched_prescriptions': searched_prescriptions,
        'all_prescriptions': all_prescriptions,
    }
    return render(request, 'prescriptions_page_manager.html', context)


def check_availability(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')  # Zmienione na POST dla bardziej spójnego działania
        if not location_id:
            return JsonResponse({'status': 'error', 'message': 'Lokalizacja nie została wybrana.'})

        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Niepoprawna lokalizacja.'})

        user = ExtendedUser.objects.get(user=request.user)
        cart_items = user.cart.items.all()  # Pobieramy leki z koszyka użytkownika

        unavailable_items = []  # Lista leków niedostępnych w lokalizacji

        for item in cart_items:
            stock = MedicationStock.objects.filter(location=location, medication=item.medication).first()
            if stock and stock.quantity >= item.quantity:
                # Lek jest dostępny w wymaganej ilości
                continue
            else:
                # Lek niedostępny lub niewystarczająca ilość
                unavailable_items.append({
                    'medication_name': item.medication.name,
                    'required_quantity': item.quantity,
                    'available_quantity': stock.quantity if stock else 0
                })
                # Dodanie do raportu brakujących leków
                report_missing_medication(location, item.medication, item.quantity)

        return JsonResponse({
            'status': 'success',
            'unavailable_items': unavailable_items
        })

def report_missing_medication(location, medication, quantity):
    # Pobierz najnowsze zamówienie PENDING lub utwórz nowe
    order = PharmacyOrder.objects.filter(
        location=location,
        status=PharmacyOrder.Status.PENDING
    ).order_by('-id').first()  # Pobiera najnowsze zamówienie

    if not order:
        order = PharmacyOrder.objects.create(
            location=location,
            status=PharmacyOrder.Status.PENDING
        )

    order_item = order.order_items.filter(medication=medication).first()
    if order_item:
        order_item.quantity += quantity
        order_item.save()
    else:
        PharmacyOrderItem.objects.create(order=order, medication=medication, quantity=quantity)
    order.save()

def create_pharmacy_order(location, medication, quantity):
    # Tworzymy nowe zamówienie, jeśli potrzebne
    order = PharmacyOrder.objects.filter(location=location).order_by('-id').first()
    if not order:
        order = PharmacyOrder.objects.create(location=location)

    # Dodajemy lek do zamówienia
    order_item = order.order_items.filter(medication=medication).first()
    if order_item:
        order_item.quantity += quantity
        order_item.save()
    else:
        PharmacyOrderItem.objects.create(order=order, medication=medication, quantity=quantity)


def add_to_stock(location, medication, quantity):
    # Dodajemy lek do magazynu
    stock, created = MedicationStock.objects.get_or_create(location=location, medication=medication)
    if created:
        stock.quantity = quantity
    else:
        stock.quantity += quantity
    stock.save()

    # Tworzymy zamówienie dla dodanych leków
    create_pharmacy_order(location, medication, quantity)


def delete_from_stock(location, medication, quantity):
    # Fetch the stock for this location and medication
    stock = MedicationStock.objects.filter(location=location, medication=medication).first()

    if stock:
        # If quantity to delete is less than or equal to current stock quantity
        if stock.quantity >= quantity:
            stock.quantity -= quantity  # Decrease the stock by the specified quantity

            # If the stock quantity becomes 0, remove it from the database
            if stock.quantity == 0:
                stock.delete()
            else:
                stock.save()  # Otherwise, save the updated stock quantity

@user_passes_test(is_manager)
def pharmacist_view(request):
    extended_user = get_object_or_404(ExtendedUser, user=request.user)
    user_location = extended_user.location  # Lokalizacja apteki

    # Pobieramy wszystkie zamówienia z lokalizacji apteki
    all_orders = Order.objects.filter(location=user_location).order_by('-date_of_order')
    for order in all_orders:
        order.set_status()

    # Pobieramy wszystkie leki dostępne w systemie
    #all_medications = Medication.objects.all()

    # pobieramy leki dostepne w danej aptece
    medications = MedicationStock.objects.filter(location=user_location)

    # Pobieramy wszystkie recepty w systemie
    all_prescriptions = Prescription.objects.all()

    # Pobieramy zamówienia brakujących leków
    pending_order = PharmacyOrder.objects.filter(location=user_location, status=PharmacyOrder.Status.PENDING).first()
    missing_medications = pending_order.order_items.all() if pending_order else []

    # Obsługa wyszukiwania recept
    search_query = request.GET.get('search', None)
    searched_prescriptions = None
    if search_query:
        searched_prescriptions = Prescription.objects.filter(
            prescription_ID=search_query
        )

    return render(request, 'manager.html', {
        'all_orders': all_orders,
        'all_prescriptions': all_prescriptions,
        'medications': medications,
        'searched_prescriptions': searched_prescriptions,
        'extended_user' : extended_user,
        'missing_medications': missing_medications,
    })

@user_passes_test(is_manager)
def place_order_for_missing_medications(request):
    if request.method == 'POST':
        medication_id = request.POST.get('medication_id')
        quantity = request.POST.get('quantity')

        # Pobierz lek na podstawie ID
        medication = get_object_or_404(Medication, id=medication_id)

        extended_user = get_object_or_404(ExtendedUser, user=request.user)
        user_location = extended_user.location

        # Tworzenie zamówienia na brakujący lek
        add_to_stock(user_location, medication, int(quantity))

        # Pobierz najnowsze zamówienie PENDING
        pending_order = PharmacyOrder.objects.filter(
            location=user_location,
            status=PharmacyOrder.Status.PENDING
        ).order_by('-id').first()  # Pracujemy tylko z najnowszym zamówieniem

        if pending_order:
                # Pobierz element zamówienia dla brakującego leku
                order_item = pending_order.order_items.filter(medication=medication).first()
                if order_item:
                    order_item.delete()

                if not pending_order.order_items.exists():
                    pending_order.status = PharmacyOrder.Status.COMPLETED
                    pending_order.save()

        return redirect('manager')
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# słownik symptomów i ich porad/lekarstw
SYMPTOM_ADVICE = {
    "ból głowy": {
        "advice": "Spróbuj odpocząć, napić się wody i unikaj stresu.",
        "medicines": ["Nurofen Express Forte 400 mg 10 kapsułek", "Paracetamol 500 mg 20 tabletek", "Ibuprom Max Sprint 400 mg kapsułki miękkie 40 szt.", "Dezamigren 12,5 mg 2 szt."]
    },
    "ból brzucha": {
        "advice": "Zaleca się spożywanie lekkostrawnych posiłków i odpoczynek.",
        "medicines": ["No-Spa Max 80 mg 24 szt.", "Espumisan kapsułki 40 mg 25szt", "Sylimarol 70 mg, drażetki 30 szt", "Ketonal 2,5% żel w tubie 100 g"]
    },
    "gorączka": {
        "advice": "Pić dużo wody, odpoczywać i stosować środki przeciwgorączkowe.",
        "medicines": ["Paracetamol 500 mg 20 tabletek", "Nurofen Express Forte 400 mg 10 kapsułek", "Nurofen dla dzieci 60 mg czopki, 10 szt."]
    },
    "kaszel":{
        "advice": "Pij dużo ciepłych napojów i unikaj zimnych napojów. Użyj syropu łagodzącego.",
        "medicines": ["Golamir 2ACT  spray do gardła 30 ml", "Theraflu ExtraGRIP 14 saszetek", "Strepsils INTENSIVE 24 tabl. do ssania", "Isla-Moos pastylki do ssania 30 szt."]
    },
    "katar":{
        "advice": "Pij dużo płynów, takich jak woda, herbaty ziołowe, czy buliony, aby rozrzedzić wydzielinę i ułatwić jej odpływ. Staraj się unikać dymu papierosowego, intensywnych zapachów, czy alergenów, które mogą nasilać objawy.",
        "medicines": ["Otrivin 0,1/%/ aerozol do nosa10 ml", "Sinupret extract 160 mg tabletki drażowane 20 szt."]
    },
    "ból stawów":{
        "advice": "Przyłóż ciepłe lub zimne okłady oraz rób łagodne ćwiczenia poprawiające ruchomość i zmniejszające napięcie.",
        "medicines": ["VOLTAREN MAX Żel - 100 g", "Sinupret extract 160 mg tabletki drażowane 20 szt.", "Ketonal 2,5% żel w tubie 100 g"]
    },
    "witaminy":{
        "advice": "Witaminy to niezbędne związki organiczne, które wspierają prawidłowe funkcjonowanie organizmu. Równowaga witaminowa jest kluczowa, dlatego warto dbać o zróżnicowaną dietę, bogatą w warzywa, owoce, ryby, nabiał i orzechy.",
        "medicines": ["Rutinoscorbin 90 tabletek powlekanych", "Centrum Energy  30szt", "Solgar Pełne Spektrum Omega 120 szt."]
    }
}

def remove_polish_chars(text):
    """Zamienia polskie znaki na ich odpowiedniki bez ogonków."""
    return unidecode.unidecode(text)

# Funkcja dopasowująca symptomy
def match_symptom(user_input):
    synonyms = {
        "ból głowy": ["ból głowy", "głowa", "migrena", "bole w glowie", "boli mnie glowa"],
        "kaszel": ["kaszel", "kaszlę", "kaszle", "mam ataki kaszlu"],
        "ból brzucha": ["brzuch", "bol brzucha", "bóle brzucha", "boli mnie brzuch", "boli brzuch"],
        "gorączka": ["gorączka", "temperatura", "mam temperature", "goraczka"],
        "katar": ["katar", "cieknie mi z nosa", "zatkany nos", "cieknie"],
        "ból stawów": ["stawy", "bolą mnie stawy", "bóle stawów"],
        "witaminy": ["witaminy", "suplementacja", "brak witamin"],
    }

    # Usuwanie polskich znaków
    user_input = remove_polish_chars(user_input.lower())

    # Rozbijanie tekstu na słowa
    tokens = re.findall(r'\b\w+\b', user_input)

    # Sprawdzanie dopasowania
    for symptom, keywords in synonyms.items():
        for keyword in keywords:
            keyword_clean = remove_polish_chars(keyword.lower())
            if any(keyword_clean in token for token in tokens):
                return symptom, SYMPTOM_ADVICE.get(symptom, "Brak szczegółowych porad.")
    
    return None, "Nie znaleziono pasujących objawów."


def symptom_advice_view(request):
    if request.method == "POST":
        user_input = request.POST.get("symptoms", "").lower()
        matched_symptom, advice_data = match_symptom(user_input)
        
        if advice_data:
            # Pobieranie leków z bazy danych
            medicines = []
            for medicine_name in advice_data["medicines"]:
                try:
                    medication = Medication.objects.get(name__iexact=medicine_name)
                    medicines.append({
                        "name": medication.name,
                        "url": f"/products/product/{medication.id}/"  # generowanie linku do widoku produktu
                    })
                except Medication.DoesNotExist:
                    # Dodajemy tylko nazwę, jeśli lek nie istnieje w bazie
                    medicines.append({"name": medicine_name, "url": None})
            
            return render(request, "symptom_advice.html", {
                "symptom": matched_symptom,
                "advice": advice_data["advice"],
                "medicines": medicines
            })
        else:
            return render(request, "symptom_advice.html", {
                "error": "Nie znaleziono porad dla podanych objawów. Spróbuj opisać je inaczej."
            })
    return render(request, "symptom_form.html")
