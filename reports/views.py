from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem
from inventory.models import Product
from finance.models import Expense
import json

@login_required
def reports_dashboard(request):
    """Main reports dashboard with overview"""
    # Get date range from request or default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Sales statistics
    sales_data = Sale.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).aggregate(
        total_sales=Sum('total_amount'),
        total_transactions=Count('id')
    )
    
    # Expenses statistics
    expenses_data = Expense.objects.filter(
        date__gte=start_date.date(),
        date__lte=end_date.date()
    ).aggregate(
        total_expenses=Sum('amount')
    )
    
    # Calculate profit
    total_sales = sales_data['total_sales'] or 0
    total_expenses = expenses_data['total_expenses'] or 0
    profit = total_sales - total_expenses
    
    # Top selling products
    top_products = SaleItem.objects.filter(
        sale__timestamp__gte=start_date
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:10]
    
    # Daily sales trend (last 7 days)
    last_7_days = timezone.now() - timedelta(days=7)
    daily_sales = Sale.objects.filter(
        timestamp__gte=last_7_days
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')
    
    # Payment method breakdown
    payment_methods = Sale.objects.filter(
        timestamp__gte=start_date
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    context = {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'profit': profit,
        'total_transactions': sales_data['total_transactions'] or 0,
        'top_products': top_products,
        'daily_sales': json.dumps(list(daily_sales), default=str),
        'payment_methods': payment_methods,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required
def sales_report(request):
    """Detailed sales report"""
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if not provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    else:
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get sales data
    sales = Sale.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).select_related('cashier').prefetch_related('items__product').order_by('-timestamp')
    
    # Calculate totals
    totals = sales.aggregate(
        total_amount=Sum('total_amount'),
        total_transactions=Count('id')
    )
    
    # Calculate average transaction
    avg_transaction = 0
    if totals['total_transactions'] and totals['total_transactions'] > 0:
        avg_transaction = totals['total_amount'] / totals['total_transactions'] if totals['total_amount'] else 0
    
    # Group by payment method
    payment_breakdown = sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Daily sales trend for the period
    daily_sales = sales.annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        total=Sum('total_amount'),
        transactions=Count('id')
    ).order_by('date')
    
    # Hourly sales pattern
    hourly_sales = sales.annotate(
        hour=TruncDate('timestamp')  # We'll use date for now, could be enhanced to hour
    ).values('hour').annotate(
        total=Sum('total_amount')
    ).order_by('hour')
    
    # Top products for the period
    top_products = SaleItem.objects.filter(
        sale__timestamp__gte=start_date,
        sale__timestamp__lte=end_date
    ).values(
        'product__name',
        'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        transactions=Count('sale', distinct=True)
    ).order_by('-total_revenue')[:10]
    
    # Category breakdown
    category_breakdown = SaleItem.objects.filter(
        sale__timestamp__gte=start_date,
        sale__timestamp__lte=end_date
    ).values('product__category__name').annotate(
        total_revenue=Sum('subtotal'),
        total_quantity=Sum('quantity'),
        transactions=Count('sale', distinct=True)
    ).order_by('-total_revenue')
    
    # Customer insights (if we had customer data)
    # For now, just transaction frequency
    transaction_frequency = {
        'total_days': (end_date.date() - start_date.date()).days + 1,
        'avg_daily_transactions': totals['total_transactions'] / max(1, (end_date.date() - start_date.date()).days + 1),
        'avg_daily_revenue': totals['total_amount'] / max(1, (end_date.date() - start_date.date()).days + 1) if totals['total_amount'] else 0
    }
    
    context = {
        'sales': sales,
        'totals': totals,
        'avg_transaction': avg_transaction,
        'payment_breakdown': payment_breakdown,
        'daily_sales': daily_sales,
        'hourly_sales': hourly_sales,
        'top_products': top_products,
        'category_breakdown': category_breakdown,
        'transaction_frequency': transaction_frequency,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/sales_report.html', context)

@login_required
def sales_report_pdf(request):
    """Generate PDF for Sales Report"""
    from shop_system.utils import render_to_pdf
    from django.http import HttpResponse
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if not provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
    else:
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get sales data
    sales = Sale.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).select_related('cashier').prefetch_related('items__product').order_by('-timestamp')
    
    # Calculate totals
    totals = sales.aggregate(
        total_amount=Sum('total_amount'),
        total_transactions=Count('id')
    )
    
    # Group by payment method
    payment_breakdown = sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    context = {
        'sales': sales,
        'totals': totals,
        'payment_breakdown': payment_breakdown,
        'start_date': start_date,
        'end_date': end_date,
        'generated_by': request.user.username,
        'now': timezone.now()
    }
    
    pdf = render_to_pdf('reports/sales_report_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Sales_Report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Rendering PDF", status=400)
@login_required
def inventory_report(request):
    """Inventory status report"""
    # Get all products with stock information
    products = Product.objects.select_related('category').all()
    
    # Calculate statistics
    total_products = products.count()
    low_stock_products = products.filter(stock_quantity__lte=F('reorder_level')).count()
    out_of_stock = products.filter(stock_quantity=0).count()
    
    # Calculate total inventory value
    total_value = sum(
        product.stock_quantity * product.buy_price 
        for product in products
    )
    
    # Group by category
    category_breakdown = products.values('category__name').annotate(
        count=Count('id'),
        total_stock=Sum('stock_quantity')
    )
    
    context = {
        'products': products,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'total_value': total_value,
        'category_breakdown': category_breakdown,
    }
    
    return render(request, 'reports/inventory_report.html', context)

@login_required
def profit_loss_report(request):
    """Profit and Loss statement"""
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to current month if not provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date.replace(day=1)
    else:
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate revenue
    sales_data = Sale.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_transactions=Count('id')
    )
    
    # Calculate cost of goods sold (COGS)
    sale_items = SaleItem.objects.filter(
        sale__timestamp__gte=start_date,
        sale__timestamp__lte=end_date
    ).select_related('product')
    
    cogs = sum(
        item.quantity * (item.product.buy_price if item.product else 0)
        for item in sale_items
    )
    
    # Get expenses
    expenses = Expense.objects.filter(
        date__gte=start_date.date(),
        date__lte=end_date.date()
    )
    
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Expense breakdown by category
    expense_breakdown = expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate profit
    total_revenue = sales_data['total_revenue'] or 0
    gross_profit = total_revenue - cogs
    net_profit = gross_profit - total_expenses
    
    # Calculate margins
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'gross_margin': gross_margin,
        'net_margin': net_margin,
        'expense_breakdown': expense_breakdown,
        'total_transactions': sales_data['total_transactions'] or 0,
    }
    
    return render(request, 'reports/profit_loss.html', context)

@login_required
def profit_loss_pdf(request):
    """Generate PDF for Profit and Loss statement"""
    from shop_system.utils import render_to_pdf
    from django.http import HttpResponse
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to current month if not provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date.replace(day=1)
    else:
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate revenue
    sales_data = Sale.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        total_transactions=Count('id')
    )
    
    # Calculate cost of goods sold (COGS)
    sale_items = SaleItem.objects.filter(
        sale__timestamp__gte=start_date,
        sale__timestamp__lte=end_date
    ).select_related('product')
    
    cogs = sum(
        item.quantity * (item.product.buy_price if item.product else 0)
        for item in sale_items
    )
    
    # Get expenses
    expenses = Expense.objects.filter(
        date__gte=start_date.date(),
        date__lte=end_date.date()
    )
    
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Expense breakdown by category
    expense_breakdown = expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate profit
    total_revenue = sales_data['total_revenue'] or 0
    gross_profit = total_revenue - cogs
    net_profit = gross_profit - total_expenses
    
    # Calculate margins
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'gross_margin': gross_margin,
        'net_margin': net_margin,
        'expense_breakdown': expense_breakdown,
        'total_transactions': sales_data['total_transactions'] or 0,
        'generated_by': request.user.username,
        'now': timezone.now()
    }
    
    pdf = render_to_pdf('reports/profit_loss_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Profit_Loss_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Rendering PDF", status=400)
