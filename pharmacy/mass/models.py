from django.contrib.auth.models import User
from django.db import models
from datetime import datetime

from django.template.defaultfilters import default


class Medication(models.Model):
    def __str__(self):
        return self.name + ' ' + str(self.price) + 'zł'

    name = models.CharField(max_length=100)
    #indications = 
    side_effects = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    description = models.TextField(null=True, blank=True)  

    image = models.ImageField(upload_to='MASS-main\image', null=True, blank=True) 


    def __str__(self):
        return f"{self.name} {self.price}"


#Recepta jest dodawana do systemu a użytkownik dodaje ją do swojego konta dzięki prescription_ID
class Prescription(models.Model):
    prescription_ID = models.DecimalField(max_digits=4, decimal_places=0)
    patient_name = models.CharField(max_length=255) # User 
    date_prescribed = models.DateField(default=datetime.now)
    medications = models.ManyToManyField(Medication)
    dosage = models.CharField(max_length=100,null=True)

    def __str__(self):
        return f"Prescription for {self.patient_name} on {self.date_prescribed}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contents = models.ManyToManyField(Medication, through='OrderItem')
    date_of_order = models.DateField(default=datetime.now)

    def __str__(self):
        return f"Order of user: {self.user}  \n Date of order:   {self.date_of_order}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.medication.name}"
    




class CartItem(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
class Cart(models.Model):
    items = models.ManyToManyField(CartItem, blank=True)


class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    prescriptions = models.ManyToManyField(Prescription, blank=True)
    user_orders = models.ManyToManyField(Order, blank=True)

    #cart = models.ManyToManyField(Medication, blank=True)

    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, null=True)
