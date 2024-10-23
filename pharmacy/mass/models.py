from django.db import models

# Create your models here.

class Medication(models.Model):
    def __str__(self):
        return self.name + ' ' + str(self.price)

    name = models.CharField(max_length=100)
    #indications = 
    side_effects = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)