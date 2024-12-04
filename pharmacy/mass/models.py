from django.contrib.auth.models import User
from django.db import models
from datetime import datetime

from django.template.defaultfilters import default


class Medication(models.Model):
    def __str__(self):
        return self.name + ' ' + str(self.price) + 'zł'

    class Category(models.TextChoices):
        PAIN = 'pain', 'Ból'
        ALLERGY ='allergy', 'Alergia'
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
    stock_quantity = models.PositiveIntegerField(default=0)
    category_tag = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)



    def __str__(self):
        return f"{self.name} {self.price}"


#Recepta jest dodawana do systemu a użytkownik dodaje ją do swojego konta dzięki prescription_ID
class Prescription(models.Model):
    prescription_ID = models.DecimalField(max_digits=4, decimal_places=0)
    patient_name = models.CharField(max_length=255) # User 
    date_prescribed = models.DateField(default=datetime.now)
    medications = models.ManyToManyField(Medication)
    #dosage = models.CharField(max_length=100,null=True)
    realized = models.BooleanField(default=False)
    added = models.BooleanField(default=False)

    def __str__(self):
        return f"Prescription for {self.patient_name} on {self.date_prescribed}"
    
    def mark_as_realized(self):
        self.realized = True
        self.save()

    def mark_as_added(self):
        self.added = True
        self.save()


class Order(models.Model):
    class Status(models.TextChoices):
        PAID = 'paid', 'Paid'
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contents = models.ManyToManyField(Medication, through='OrderItem')
    date_of_order = models.DateField(default=datetime.now)
    shipping_address = models.CharField(max_length=255,default="")
    phone_number = models.DecimalField(max_digits=9, decimal_places=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    total = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    payment_method = models.TextField(default="")

    def calculate_total(self):
        total = sum(item.subtotal() for item in self.order_items.all())
        return total

    def __str__(self):
        return f"{self.user.username} {self.date_of_order} {self.shipping_address} {self.phone_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def subtotal(self):
        return self.quantity * self.medication.price
    def __str__(self):
        return f"{self.quantity} of {self.medication.name}"
    

class CartItem(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    #medication_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    
class Cart(models.Model):
    items = models.ManyToManyField(CartItem, blank=True)


class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    prescriptions = models.ManyToManyField(Prescription, blank=True)
    user_orders = models.ManyToManyField(Order, blank=True)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True, related_name='user_cart')
    prescription_cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True, related_name='prescription_user_cart')
