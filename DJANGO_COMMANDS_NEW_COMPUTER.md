# Django commands to run this project on a new computer (Windows/PowerShell)

> Project root: `AL SHOP MANAGEMENT SYSTEM/`
> Django project folder: `AL SHOP MANAGEMENT SYSTEM/ML DJANGO/`

## 1) Go to the Django project folder

```powershell
cd "c:\path\to\AL SHOP MANAGEMENT SYSTEM"
cd "ML DJANGO"
```

## 2) Create + activate a virtual environment (recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, run this once (CurrentUser only), then re-run activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 3) Install Python packages (Django + PDF support)

```powershell
pip install "Django>=5,<6" xhtml2pdf
```

## 4) Create/upgrade the database (apply migrations)

```powershell
python manage.py migrate
```

## 5) (Optional) Seed sample data + default accounts

```powershell
python manage.py seed_data
```

## 6) Run the server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/login/
```

## Extra useful Django commands (optional)

```powershell
# Create an admin user (if you don't use seed_data)
python manage.py createsuperuser

# If you change models
python manage.py makemigrations
python manage.py migrate

# Quick health check
python manage.py check

# Run tests (if you add/maintain tests)
python manage.py test
```

