from django.db import models
from users.models import CustomUser

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Expense Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    description = models.TextField(blank=True)
    date = models.DateField()
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - TSh {self.amount}"


class ShopSettings(models.Model):
    """Singleton model to store shop information editable via admin."""
    name = models.CharField(max_length=200, default='My Shop')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    logo_url = models.CharField(max_length=500, blank=True, help_text='URL to shop logo (optional)')

    class Meta:
        verbose_name = 'Shop Settings'

    def __str__(self):
        return 'Shop Settings'
