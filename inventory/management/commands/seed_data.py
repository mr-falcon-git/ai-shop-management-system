from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random

from users.models import CustomUser
from inventory.models import Category, Supplier, Product
from finance.models import ExpenseCategory, Expense
from sales.models import Sale, SaleItem

class Command(BaseCommand):
    help = 'Seed the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # Users
        admin, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if admin and not admin.check_password('adminpass'):
            admin.set_password('adminpass')
            admin.save()

        cashier, _ = CustomUser.objects.get_or_create(
            username='cashier1',
            defaults={'email': 'cashier1@example.com', 'role': 'cashier'}
        )
        if cashier and not cashier.check_password('cashierpass'):
            cashier.set_password('cashierpass')
            cashier.save()

        # Categories
        categories = []
        for name in ['Beverages', 'Snacks', 'Household', 'Personal Care']:
            c, _ = Category.objects.get_or_create(name=name, defaults={'description': f'{name} products'})
            categories.append(c)

        # Suppliers
        suppliers = []
        for i in range(1,4):
            s, _ = Supplier.objects.get_or_create(name=f'Supplier {i}', defaults={
                'phone': f'000-000-000{i}', 'email': f'supplier{i}@example.com'
            })
            suppliers.append(s)

        # Products
        products = []
        sample_products = [
            ('Coke 500ml', '1234560001', 'Beverages', 0.50, 1.00, 100),
            ('Mineral Water 1L', '1234560002', 'Beverages', 0.30, 0.80, 200),
            ('Potato Chips', '1234560003', 'Snacks', 0.40, 1.20, 150),
            ('Laundry Soap', '1234560004', 'Household', 1.00, 2.50, 50),
            ('Toothpaste', '1234560005', 'Personal Care', 0.80, 2.00, 75),
        ]
        for name, barcode, cat_name, buy, sell, qty in sample_products:
            cat = Category.objects.get(name=cat_name)
            supp = random.choice(suppliers)
            p, _ = Product.objects.get_or_create(barcode=barcode, defaults={
                'name': name,
                'category': cat,
                'supplier': supp,
                'description': name,
                'unit': 'pcs',
                'buy_price': Decimal(str(buy)),
                'sell_price': Decimal(str(sell)),
                'stock_quantity': qty,
                'reorder_level': 10
            })
            products.append(p)

        # Expense categories and expenses
        exp_cat, _ = ExpenseCategory.objects.get_or_create(name='Utilities')
        Expense.objects.create(title='Electricity Bill', amount=Decimal('50.00'), category=exp_cat,
                               description='Monthly electricity', date=timezone.now().date(), added_by=admin)

        # Sample sales
        today = timezone.now()
        for i in range(5):
            sale = Sale.objects.create(cashier=cashier, payment_method=random.choice(['cash','card']), total_amount=0)
            total = Decimal('0.00')
            items = random.sample(products, k=2)
            for prod in items:
                qty = random.randint(1,5)
                price = prod.sell_price
                subtotal = Decimal(qty) * price
                SaleItem.objects.create(sale=sale, product=prod, quantity=qty, price_at_sale=price, subtotal=subtotal)
                prod.stock_quantity = max(0, prod.stock_quantity - qty)
                prod.save()
                total += subtotal
            sale.total_amount = total
            sale.save()

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
