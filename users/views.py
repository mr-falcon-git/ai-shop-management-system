from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, F
from datetime import timedelta
from sales.models import Sale, SaleItem
from inventory.models import Product, Category
from ai_engine.analysis import AIAnalyzer

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Today's Sales
    todays_sales = Sale.objects.filter(timestamp__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Total Products
    total_products = Product.objects.count()
    
    # Low Stock Items
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('reorder_level')).count()
    
    # Monthly Revenue
    monthly_revenue = Sale.objects.filter(timestamp__date__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Sales Trend (Last 7 Days)
    seven_days_ago = today - timedelta(days=6)
    sales_trend = []
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        total = Sale.objects.filter(timestamp__date=date).aggregate(total=Sum('total_amount'))['total'] or 0
        sales_trend.append({'date': date.strftime('%a'), 'total': float(total)})
    
    # Top Categories (by sales in last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    top_categories = SaleItem.objects.filter(
        sale__timestamp__date__gte=thirty_days_ago
    ).values('product__category__name').annotate(
        total_sales=Sum('subtotal')
    ).order_by('-total_sales')[:5]
    
    # AI Insights
    analyzer = AIAnalyzer()
    insights = analyzer.get_product_recommendations()[:3]  # Get top 3 recommendations
    
    context = {
        'user': request.user,
        'todays_sales': todays_sales,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'monthly_revenue': monthly_revenue,
        'sales_trend': sales_trend,
        'top_categories': top_categories,
        'insights': insights,
    }
    return render(request, 'dashboard.html', context)
