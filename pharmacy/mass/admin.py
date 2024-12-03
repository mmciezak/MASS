from django.contrib import admin

# Register your models here.

from .models import Medication, Prescription, Order, ExtendedUser, Cart, CartItem


admin.site.register(Medication)
admin.site.register(Prescription)
admin.site.register(Order)

admin.site.register(ExtendedUser)
admin.site.register(Cart)
admin.site.register(CartItem)



class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'date_prescribed', 'dosage')
    search_fields = ('patient_name',)
    list_filter = ('date_prescribed',)
    filter_horizontal = ('medications',)