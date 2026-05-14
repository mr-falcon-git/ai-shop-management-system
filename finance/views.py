from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay, TruncYear
from django.conf import settings
from sales.models import Sale
from .models import Expense, ExpenseCategory
from .models import ShopSettings
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse

@login_required
def expense_list(request):
    """List all expenses with filtering"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_id = request.GET.get('category')
    
    # Base queryset
    expenses = Expense.objects.select_related('category', 'added_by').all()
    
    # Apply filters
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    
    # Calculate total
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get all categories for filter dropdown
    categories = ExpenseCategory.objects.all()
    
    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'categories': categories,
        'selected_category': category_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'finance/expense_list.html', context)

@login_required
def expense_create(request):
    """Create a new expense"""
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        date = request.POST.get('date')
        
        try:
            expense = Expense.objects.create(
                title=title,
                amount=amount,
                category_id=category_id if category_id else None,
                description=description,
                date=date,
                added_by=request.user
            )
            messages.success(request, f'Expense "{title}" added successfully!')
            return redirect('expense_list')
        except Exception as e:
            messages.error(request, f'Error creating expense: {str(e)}')
    
    categories = ExpenseCategory.objects.all()
    context = {
        'categories': categories,
        'today': timezone.now().date(),
    }
    
    return render(request, 'finance/expense_form.html', context)

@login_required
def expense_update(request, pk):
    """Update an existing expense"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        expense.title = request.POST.get('title')
        expense.amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        expense.category_id = int(category_id) if category_id else None
        expense.description = request.POST.get('description', '')
        expense.date = request.POST.get('date')
        
        try:
            expense.save()
            messages.success(request, f'Expense "{expense.title}" updated successfully!')
            return redirect('expense_list')
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    categories = ExpenseCategory.objects.all()
    context = {
        'expense': expense,
        'categories': categories,
        'is_update': True,
    }
    
    return render(request, 'finance/expense_form.html', context)

@login_required
def expense_delete(request, pk):
    """Delete an expense"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f'Expense "{title}" deleted successfully!')
        return redirect('expense_list')
    
    context = {
        'expense': expense,
    }
    
    return render(request, 'finance/expense_confirm_delete.html', context)

@login_required
def expense_dashboard(request):
    """Expense analytics dashboard"""
    # Get date range (default to current month)
    today = timezone.now()
    start_date = today.replace(day=1)
    end_date = today
    
    # Get expenses for the period
    expenses = Expense.objects.filter(
        date__gte=start_date.date(),
        date__lte=end_date.date()
    )
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_count = expenses.count()
    
    # Category breakdown
    category_breakdown = expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Monthly trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_expenses = Expense.objects.filter(
        date__gte=six_months_ago.date()
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Recent expenses
    recent_expenses = Expense.objects.select_related('category', 'added_by').order_by('-date')[:10]
    
    context = {
        'total_expenses': total_expenses,
        'expense_count': expense_count,
        'category_breakdown': category_breakdown,
        'monthly_expenses': monthly_expenses,
        'recent_expenses': recent_expenses,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'finance/expense_dashboard.html', context)

@login_required
def category_list(request):
    """List all expense categories"""
    categories = ExpenseCategory.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'finance/category_list.html', context)

@login_required
def category_create(request):
    """Create a new expense category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        try:
            ExpenseCategory.objects.create(
                name=name,
                description=description
            )
            messages.success(request, f'Category "{name}" created successfully!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    
    return render(request, 'finance/category_form.html', {})

@login_required
def category_update(request, pk):
    """Update an expense category"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description', '')
        
        try:
            category.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    context = {
        'category': category,
        'is_update': True,
    }
    
    return render(request, 'finance/category_form.html', context)

@login_required
def category_delete(request, pk):
    """Delete an expense category"""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('category_list')
    
    context = {
        'category': category,
    }
    
    return render(request, 'finance/category_confirm_delete.html', context)

@login_required
def expense_list_pdf(request):
    """Generate PDF report of expenses"""
    # Get filter parameters (same as list view)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_id = request.GET.get('category')
    
    # Base queryset
    expenses = Expense.objects.select_related('category', 'added_by').all().order_by('-date')
    
    # Apply filters
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    if category_id:
        expenses = expenses.filter(category_id=category_id)
        
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'start_date': start_date,
        'end_date': end_date,
        'generated_by': request.user.username,
        'now': timezone.now()
    }
    
    from shop_system.utils import render_to_pdf

    pdf = render_to_pdf('finance/expense_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Expense_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Rendering PDF", status=400)


@login_required
def finance_overview(request):
    """Show income, expenses and profit/loss by period and allow PDF export."""
    period = request.GET.get('period', 'monthly')  # daily, monthly, annual
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = timezone.now()
    if not start_date and not end_date:
        # Defaults: month to date for monthly, today for daily, year-to-date for annual
        if period == 'daily':
            start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end = today
        elif period == 'annual':
            start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today
        else:
            # monthly
            start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = today
    else:
        # parse provided dates (expecting YYYY-MM-DD)
        try:
            start = datetime.fromisoformat(start_date) if start_date else today.replace(day=1)
        except Exception:
            start = today.replace(day=1)
        try:
            end = datetime.fromisoformat(end_date) if end_date else today
        except Exception:
            end = today

    # Sales (income)
    sales_qs = Sale.objects.filter(timestamp__gte=start, timestamp__lte=end)
    income_total = sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0

    # Expenses
    expenses_qs = Expense.objects.filter(date__gte=start.date(), date__lte=end.date())
    expenses_total = expenses_qs.aggregate(total=Sum('amount'))['total'] or 0

    profit = income_total - expenses_total
    profit_percent = (profit / income_total * 100) if income_total else None

    # Breakdown series for charts/tables
    if period == 'daily':
        income_series = sales_qs.annotate(day=TruncDay('timestamp')).values('day').annotate(total=Sum('total_amount')).order_by('day')
        expense_series = expenses_qs.annotate(day=TruncDay('date')).values('day').annotate(total=Sum('amount')).order_by('day')
    elif period == 'annual':
        income_series = sales_qs.annotate(year=TruncYear('timestamp')).values('year').annotate(total=Sum('total_amount')).order_by('year')
        expense_series = expenses_qs.annotate(year=TruncYear('date')).values('year').annotate(total=Sum('amount')).order_by('year')
    else:
        income_series = sales_qs.annotate(month=TruncMonth('timestamp')).values('month').annotate(total=Sum('total_amount')).order_by('month')
        expense_series = expenses_qs.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

    context = {
        'period': period,
        'start': start,
        'end': end,
        'income_total': income_total,
        'expenses_total': expenses_total,
        'profit': profit,
        'profit_percent': profit_percent,
        'income_series': income_series,
        'expense_series': expense_series,
        'generated_by': request.user.username,
        'now': timezone.now(),
        'shop_name': getattr(settings, 'SHOP_NAME', 'My Shop'),
        'shop_address': getattr(settings, 'SHOP_ADDRESS', ''),
        'shop_logo_url': getattr(settings, 'SHOP_LOGO_URL', ''),
        'currency': getattr(settings, 'CURRENCY', 'TSh'),
    }

    # Override with ShopSettings if available
    try:
        shop = ShopSettings.objects.first()
        if shop:
            context['shop_name'] = shop.name or context['shop_name']
            context['shop_address'] = shop.address or context['shop_address']
            context['shop_logo_url'] = shop.logo_url or context['shop_logo_url']
            context['currency'] = context.get('currency')
            context['shop_phone'] = shop.phone or context.get('shop_phone', '')
            context['shop_email'] = shop.email or context.get('shop_email', '')
    except Exception:
        pass

    if request.GET.get('export') == 'pdf':
        from shop_system.utils import render_to_pdf

        pdf = render_to_pdf('finance/finance_report_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Finance_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error Rendering PDF", status=400)

    return render(request, 'finance/finance_report.html', context)
