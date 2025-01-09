from django.contrib import admin

# Register your models here.

from .models import Medication, Prescription, Order, ExtendedUser, Cart, CartItem, Location, MedicationStock, Symptom
#from .models import PrescriptionTest

admin.site.register(Medication)
admin.site.register(Prescription)
admin.site.register(Order)

admin.site.register(ExtendedUser)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Location)
admin.site.register(MedicationStock)


#admin.site.register(PrescriptionTest)

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'date_prescribed', 'dosage')
    search_fields = ('patient_name',)
    list_filter = ('date_prescribed',)
    filter_horizontal = ('medications',)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name',)

class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    filter_horizontal = ('symptoms',)