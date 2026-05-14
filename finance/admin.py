from django.contrib import admin
from .models import ExpenseCategory, Expense, ShopSettings

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'date', 'added_by']
    list_filter = ['category', 'date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')

    def has_add_permission(self, request):
        # Allow creating only one ShopSettings instance
        return not ShopSettings.objects.exists()
