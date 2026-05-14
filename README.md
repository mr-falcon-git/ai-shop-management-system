# AL Shop Management System (Django)

This is a Django-based shop management system with:
- Inventory (products, categories, suppliers, stock levels)
- Sales / POS (real sales tracking + automatic stock deduction)
- Reports + PDFs
- Finance (income vs expenses)
- AI Insights (sales forecast, stock-out prediction, anomalies)

The Django project lives in `ML DJANGO/`.

## Requirements

- Windows + PowerShell (recommended)
- Python 3.11+ (tested here with Python 3.13)
- Django 5.x
- `xhtml2pdf` (for PDF receipts/reports)

## Setup (first time)

Open PowerShell in the project folder, then run:

```powershell
cd "ML DJANGO"

# Optional but recommended
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install django xhtml2pdf

python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Then open:
- `http://127.0.0.1:8000/login/`

## Login (Default Accounts)

The login screen uses **Username + Password** (not email).

**Admin**
- Username: `admin`
- Email: `admin@example.com`
- Password: `adminpass`

**Cashier**
- Username: `cashier1`
- Email: `cashier1@example.com`
- Password: `cashierpass`

### Change / Create Users

- Create a new admin account:

```powershell
cd "ML DJANGO"
python manage.py createsuperuser
```

- Reset seeded accounts back to the default passwords:

```powershell
cd "ML DJANGO"
python manage.py seed_data
```

## How To Use (Quick Guide)

### 1) Inventory

Go to **Inventory** to manage products.
- Add/edit products (barcode, buy price, sell price, stock quantity, reorder level)
- Low stock is automatically detected using `stock_quantity <= reorder_level`

### 2) Sales / POS (Sales Tracking)

Go to **Sales / POS**:
1. Search products by barcode or name
2. Add items to cart and set quantities
3. Choose payment method (cash/card/mobile)
4. Complete the sale

What happens when you complete a sale:
- A `Sale` record is created
- `SaleItem` records are created for each product
- Product stock is reduced immediately
- The system saves the sale total and you can view it in **Sales History**

You can open a sale and download/print a PDF receipt from the sale detail page.

### 3) Reports

Go to **Reports** to see:
- Sales totals and transactions for a date range
- Top products
- Profit/loss views (income, COGS, expenses)

Some report pages include a button to send report data to the **AI Insights** dashboard.

### 4) Expenses + Finance

Go to **Expenses** to add operational costs.

Go to **Finance** to view:
- Income (from Sales)
- Expenses
- Profit / loss
- Optional PDF export

### 5) AI Insights (Predictions)

Go to **AI Insights**:
- **7‑Day Sales Forecast**: uses the last ~30 days of daily sales to predict future revenue
- **Stock‑out Predictions**: estimates which products may run out soon based on recent sales velocity
- **Anomalies**: flags unusual spikes/drops compared to recent averages
- Dashboard charts are based on your real sales/inventory data (if you have no sales yet, charts will be empty/neutral)

## Admin Panel

Admins can access:
- `http://127.0.0.1:8000/admin/`

Use it to manage users, products, sales, expenses, etc.

## Common Commands

```powershell
cd "ML DJANGO"
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Notes

- Database is SQLite: `ML DJANGO/db.sqlite3`
- If you change models, run: `python manage.py makemigrations` then `python manage.py migrate`
