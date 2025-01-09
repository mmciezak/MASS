from django.contrib.auth.models import User
from django.db import models
from datetime import datetime




class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    advice = models.TextField()

    def __str__(self):
        return self.name


class Medication(models.Model):
    def __str__(self):
        return self.name + ' ' + str(self.price) + 'zł'

    class Category(models.TextChoices):
        PAIN = 'pain', 'Ból'
        ALLERGY = 'allergy', 'Alergia'
        DIABETIC = 'diabetic', 'Diabetyk'
        SKIN = 'skin', 'Skóra'
        COLD = 'cold', 'Przeziębienie'
        WOUNDS = 'wounds', 'Rany i oparzenia'
        DIGESTIVE = 'digestive', 'Trawienie'
        CONTRACEPTION = 'contraception', 'Antykoncepcja'
        VITAMINS = 'vitamins', 'Witaminy'
        OTHER = 'inne', 'Inne'

    name = models.CharField(max_length=100)
    side_effects = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='MASS-main\image', null=True, blank=True)
    #stock_quantity = models.PositiveIntegerField(default=0)
    category_tag = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    #symptoms = models.ManyToManyField(Symptom, related_name='medications')
    


class Location(models.Model):
    address = models.CharField(max_length=255, default="")

    def __str__(self):
        return f"{self.address}"
    
class MedicationStock(models.Model): # do kazdej lokacji bedzie przypisana okreslona ilosc towaru
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE) #polaczenie z apteka
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0) #ilosc zarezerwowanych lekow(przy reserved==quantity nie mozna zamowiec tego leku)

    class Meta:
        unique_together = ('medication', 'location')

    def __str__(self):
        return f"{self.quantity}x {self.medication.name} at {self.location.address}"
    
    def report(self): #raport
        return f"{self.location.address} pharmacy stock for {self.medication.name}: {self.quantity}. \nReserved: {self.reserved}"
    
    def out_of_stock(self): # zwraca true jesli nie ma juz leku
        if self.quantity==0 or self.reserved==self.quantity:
            return True
        return False

    def can_sell(self, requested_quantity):
        available_quantity = self.quantity - self.reserved
        return available_quantity >= requested_quantity

    def reserve(self, quantity):
        if self.can_sell(quantity):
            self.reserved += quantity
            self.save()
            return True
        return False

    def unreserve(self, quantity):
        if quantity <= self.reserved:
            self.reserved -= quantity
            self.save()
            return True
        return False

    def sell(self, quantity):
        if quantity > 0 and self.can_sell(quantity):
            self.quantity -= quantity
            self.save()
            return True
        return False

    def realize_reservation(self, quantity):
        if quantity <= self.reserved and quantity <= self.quantity:
            self.reserved -= quantity
            self.quantity -= quantity
            self.save()
            return True
        return False


class CartItem(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    # medication_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.medication.name} x{self.quantity}"

# Recepta jest dodawana do systemu a użytkownik dodaje ją do swojego konta dzięki prescription_ID
#from django.contrib.postgres.fields import ArrayField
class Prescription(models.Model):
    prescription_ID = models.DecimalField(max_digits=4, decimal_places=0)
    patient_name = models.CharField(max_length=255)  # User
    date_prescribed = models.DateField(default=datetime.now)
    medications = models.ManyToManyField(Medication)
    #medications = models.ManyToManyField(CartItem) # cart item zeby byla mozliwosc dodawania lekow w ilosci
    # dosage = models.CharField(max_length=100,null=True)
    #quantities = ArrayField(models.IntegerField(), blank=True, default=list)
    quantities = models.JSONField(blank=True, null=True, default=None)
    #quantities = models.JSONField(blank=True, default="[]")
    realized = models.BooleanField(default=False)
    added = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.prescription_ID} Prescription for {self.patient_name} on {self.date_prescribed}"

    def mark_as_realized(self):
        self.realized = True
        self.save()

    def mark_as_added(self):
        self.added = True
        self.save()



from datetime import datetime, timedelta

def default_expiry_date():
    return datetime.now().date() + timedelta(days=7)

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RECEIVED = 'received', 'Received'
        EXPIRED = 'expired', 'Expired'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contents = models.ManyToManyField(Medication, through='OrderItem')
    date_of_order = models.DateField(default=datetime.now)
    shipping_address = models.CharField(max_length=255, default="")
    phone_number = models.DecimalField(max_digits=20, decimal_places=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    expiry_date = models.DateField(default=default_expiry_date) # klient ma 7 dni na odebranie zamowienia, potem ustawia sie na 'expired'

    def calculate_total(self):
        total = sum(item.subtotal() for item in self.order_items.all())
        return total

    def __str__(self):
        return f"{self.user.username} {self.date_of_order} {self.shipping_address} {self.phone_number}"
    
    def set_status(self):
        if datetime.now().date()>self.expiry_date:
            self.status = self.Status.EXPIRED
    
    def receive_order(self): # oznacza zamowienie jako zreailzowane
        self.status = self.Status.RECEIVED



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def subtotal(self):
        return self.quantity * self.medication.price

    def __str__(self):
        return f"{self.quantity} of {self.medication.name}"



class Cart(models.Model):
    items = models.ManyToManyField(CartItem, blank=True)


class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    prescriptions = models.ManyToManyField(Prescription, blank=True)
    user_orders = models.ManyToManyField(Order, blank=True)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True, related_name='user_cart')
    prescription_cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True,
                                             related_name='prescription_user_cart')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    is_manager = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    




