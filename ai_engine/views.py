from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .analysis import AIAnalyzer
from inventory.models import Product
from sales.models import Sale, SaleItem
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
def ai_dashboard(request):
    analyzer = AIAnalyzer()

    # Live system metrics
    system_start_date = timezone.now().date() - timedelta(days=30)
    total_sales_30d = Sale.objects.filter(timestamp__date__gte=system_start_date).aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions_30d = Sale.objects.filter(timestamp__date__gte=system_start_date).count()
    avg_transaction_30d = total_sales_30d / total_transactions_30d if total_transactions_30d else 0
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('reorder_level')).count()
    top_categories_system = SaleItem.objects.filter(
        sale__timestamp__date__gte=system_start_date,
        product__category__isnull=False
    ).values('product__category__name').annotate(
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:5]

    system_data = {
        'total_sales_30d': float(total_sales_30d),
        'total_transactions_30d': total_transactions_30d,
        'avg_transaction_30d': float(avg_transaction_30d),
        'total_products': Product.objects.count(),
        'low_stock_count': low_stock_count,
        'top_categories': list(top_categories_system),
        'period_label': f"Last 30 days ({system_start_date} → {timezone.now().date()})",
    }

    # Always use live system data for AI analysis.
    lookback_days = 30
    forecast_days = 7
    forecast = analyzer.get_sales_forecast(days=forecast_days, lookback_days=lookback_days)
    stock_predictions = analyzer.get_low_stock_predictions()
    top_products = analyzer.get_top_products(lookback_days=lookback_days, limit=5)
    revenue_trend = analyzer.get_revenue_trend(days=min(14, lookback_days))
    inventory_health = analyzer.get_inventory_health(lookback_days=lookback_days)
    recommendations = analyzer.get_product_recommendations()
    anomalies = analyzer.get_anomalies()
    fed_insights = []
    
    # Prepare chart data
    forecast_dates = [item['date'].strftime('%Y-%m-%d') for item in forecast]
    forecast_values = [item['predicted_amount'] for item in forecast]
    forecast_lowers = [item.get('lower') for item in forecast]
    forecast_uppers = [item.get('upper') for item in forecast]

    top_product_labels = [p['name'] for p in top_products]
    top_product_values = [p['total_revenue'] for p in top_products]

    revenue_trend_dates = [row['date'].strftime('%Y-%m-%d') for row in revenue_trend]
    revenue_trend_values = [row['total'] for row in revenue_trend]

    radar_labels = ['Stock Level', 'Turnover Rate', 'Demand', 'Profit Margin', 'Availability']
    radar_values = [
        inventory_health.get('stock_level', 0),
        inventory_health.get('turnover_rate', 0),
        inventory_health.get('demand', 0),
        inventory_health.get('profit_margin', 0),
        inventory_health.get('availability', 0),
    ]
    
    # Forecast summary based on actual prediction data
    if forecast:
        next_forecast = forecast[0]
        historical_dates, historical_values = analyzer._get_daily_revenue_series(lookback_days=30)
        historical_avg = sum(historical_values) / len(historical_values) if historical_values else 0
        change_pct = ((next_forecast['predicted_amount'] - historical_avg) / historical_avg * 100) if historical_avg else 0
        if change_pct > 5:
            forecast_signal = 'Increasing'
        elif change_pct < -5:
            forecast_signal = 'Decreasing'
        else:
            forecast_signal = 'Stable'
        forecast_summary = {
            'next_date': next_forecast['date'].strftime('%Y-%m-%d'),
            'next_value': next_forecast['predicted_amount'],
            'average_value': round(sum(f['predicted_amount'] for f in forecast) / len(forecast), 2),
            'trend': forecast_signal,
            'change_pct': round(change_pct, 1),
            'direction': 'up' if change_pct > 0 else ('down' if change_pct < 0 else 'flat')
        }
    else:
        forecast_summary = {
            'next_date': None,
            'next_value': 0,
            'average_value': 0,
            'trend': 'No data',
            'change_pct': 0,
            'direction': 'flat'
        }

    # AI action recommendation based on forecast and system data
    if forecast_summary['trend'] == 'Increasing':
        ai_action = {
            'title': 'Prepare for rising demand',
            'message': 'Forecast predicts increasing sales. Reorder low-stock items and prioritize fast-moving categories.',
            'severity': 'positive'
        }
    elif forecast_summary['trend'] == 'Decreasing':
        ai_action = {
            'title': 'Demand slowing down',
            'message': 'Sales are predicted to ease. Consider promotions on slower-moving products to keep inventory moving.',
            'severity': 'warning'
        }
    else:
        ai_action = {
            'title': 'Maintain current stock strategy',
            'message': 'Forecast is stable. Continue monitoring daily sales and replenish items as usual.',
            'severity': 'neutral'
        }

    # Calculate additional metrics
    total_products = Product.objects.count()
    total_insights = len(stock_predictions) + len(recommendations) + len(anomalies)

    # Risk level (simple heuristic)
    critical_count = sum(1 for p in stock_predictions if p.get('status') == 'Critical')
    negative_anomalies = sum(1 for a in anomalies if a.get('severity') == 'Negative')
    risk_score = (critical_count * 3) + (max(0, len(stock_predictions) - critical_count)) + (negative_anomalies * 2)
    if risk_score >= 8:
        risk_level = 'High'
    elif risk_score >= 3:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    context = {
        'forecast': forecast,
        'stock_predictions': stock_predictions,
        'recommendations': recommendations,
        'anomalies': anomalies,
        'fed_insights': fed_insights,
        'forecast_dates': forecast_dates,
        'forecast_values': forecast_values,
        'forecast_lowers': forecast_lowers,
        'forecast_uppers': forecast_uppers,
        'top_product_labels': top_product_labels,
        'top_product_values': top_product_values,
        'revenue_trend_dates': revenue_trend_dates,
        'revenue_trend_values': revenue_trend_values,
        'radar_labels': radar_labels,
        'radar_values': radar_values,
        'forecast_summary': forecast_summary,
        'ai_action': ai_action,
        'total_products': total_products,
        'total_insights': total_insights,
        'risk_level': risk_level,
        'system_data': system_data,
    }

    return render(request, 'ai_engine/dashboard.html', context)



@login_required
def chatbot(request):
    """Chatbot interface for querying product availability."""
    return render(request, 'ai_engine/chatbot.html')


@csrf_exempt
@login_required
def chatbot_query(request):
    """Handle chatbot queries for product information."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        query = data.get('query', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if not query:
        return JsonResponse({'response': 'Please ask me about a product!'})
    
    # Get current date and time
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Search for products (case insensitive)
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query)
    )
    
    if not products.exists():
        return JsonResponse({'response': f"Sorry, I couldn't find any products matching '{query}'.\n\n📅 Checked on: {current_datetime}"})
    
    responses = []
    for product in products:
        if product.stock_quantity > 0:
            response = f"✅ {product.name} is available!\n💰 Price: {product.sell_price} Tsh\n📦 Remaining stock: {product.stock_quantity} {product.unit}"
        else:
            response = f"❌ {product.name} is currently out of stock."
        responses.append(response)
    
    final_response = '\n\n'.join(responses) + f"\n\n📅 Information as of: {current_datetime}"
    return JsonResponse({'response': final_response})
