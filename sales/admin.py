from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['subtotal']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'cashier', 'total_amount', 'payment_method', 'timestamp']
    list_filter = ['payment_method', 'timestamp']
    inlines = [SaleItemInline]
    readonly_fields = ['timestamp']
