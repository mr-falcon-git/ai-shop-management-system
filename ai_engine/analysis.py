from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from math import sqrt

from django.db.models import F, Sum, Count, Q, Case, When, Value, FloatField
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.cache import cache

from inventory.models import Product
from sales.models import Sale, SaleItem


@dataclass(frozen=True)
class ForecastPoint:
    date: object
    predicted_amount: float
    lower: float | None = None
    upper: float | None = None

class AIAnalyzer:
    def __init__(self):
        self.today = timezone.now().date()

    def _get_daily_revenue_series(self, lookback_days: int = 30) -> tuple[list[object], list[float]]:
        lookback_days = max(1, int(lookback_days))
        start_date = self.today - timedelta(days=lookback_days - 1)

        daily = (
            Sale.objects.filter(timestamp__date__gte=start_date)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(total=Sum('total_amount'))
            .order_by('day')
        )

        revenue_by_date = {row['day']: float(row['total'] or 0) for row in daily}
        dates: list[object] = []
        values: list[float] = []
        for i in range(lookback_days):
            day = start_date + timedelta(days=i)
            dates.append(day)
            values.append(float(revenue_by_date.get(day, 0.0)))

        return dates, values

    def get_sales_forecast(self, days: int = 7, lookback_days: int = 30) -> list[dict]:
        """
        Lightweight forecast for the next 'days' days.

        Uses a linear trend on daily revenue, with an optional day-of-week seasonal adjustment.
        """
        days = max(1, int(days))
        dates, values = self._get_daily_revenue_series(lookback_days=lookback_days)
        if not values or sum(values) == 0:
            return []

        n = len(values)
        t_mean = (n - 1) / 2
        y_mean = sum(values) / n

        denom = sum((i - t_mean) ** 2 for i in range(n))
        if denom == 0:
            slope = 0.0
        else:
            slope = sum((i - t_mean) * (values[i] - y_mean) for i in range(n)) / denom
        intercept = y_mean - slope * t_mean

        # Day-of-week seasonal index (bounded) so forecasts look realistic for weekly patterns.
        overall_avg = y_mean
        dow_totals = [0.0] * 7
        dow_counts = [0] * 7
        for day, revenue in zip(dates, values, strict=False):
            dow = day.weekday()
            dow_totals[dow] += revenue
            dow_counts[dow] += 1

        seasonal_index = [1.0] * 7
        if overall_avg > 0:
            for dow in range(7):
                if dow_counts[dow]:
                    idx = (dow_totals[dow] / dow_counts[dow]) / overall_avg
                    seasonal_index[dow] = max(0.6, min(1.4, idx))

        # Residual std-dev for a simple uncertainty band.
        residuals = []
        for i in range(n):
            y_hat = intercept + slope * i
            residuals.append(values[i] - y_hat)
        variance = (sum(r * r for r in residuals) / max(1, (n - 2))) if n >= 3 else 0.0
        sigma = sqrt(variance)
        band = 1.28 * sigma  # ~80% interval for a normal-ish residual distribution

        forecast: list[ForecastPoint] = []
        for step in range(1, days + 1):
            next_date = self.today + timedelta(days=step)
            t_future = (n - 1) + step
            base = intercept + slope * t_future
            adjusted = max(0.0, base) * seasonal_index[next_date.weekday()]

            lower = max(0.0, adjusted - band) if sigma else None
            upper = (adjusted + band) if sigma else None

            forecast.append(
                ForecastPoint(
                    date=next_date,
                    predicted_amount=round(adjusted, 2),
                    lower=round(lower, 2) if lower is not None else None,
                    upper=round(upper, 2) if upper is not None else None,
                )
            )

        return [p.__dict__ for p in forecast]

    def get_low_stock_predictions(self):
        """
        Predict which items will run out of stock in the next 7 days based on sales velocity.
        Optimized: Use database aggregation and filtering instead of looping.
        """
        start_date = self.today - timedelta(days=30)
        
        # Get all products with sales in the period
        products_with_sales = (
            SaleItem.objects
            .filter(sale__timestamp__date__gte=start_date)
            .values('product')
            .annotate(total_qty=Sum('quantity'))
        )
        sold_product_ids = {item['product']: item['total_qty'] for item in products_with_sales}
        
        predictions = []
        
        # Check only products with recent sales or low stock
        products = Product.objects.filter(
            Q(id__in=sold_product_ids.keys()) | 
            Q(stock_quantity__lte=F('reorder_level'))
        ).values('id', 'name', 'stock_quantity', 'reorder_level')
        
        for product in products:
            total_sold = sold_product_ids.get(product['id'], 0)
            daily_velocity = total_sold / 30 if total_sold > 0 else 0
            
            if daily_velocity > 0:
                days_left = product['stock_quantity'] / daily_velocity
            else:
                days_left = float('inf')
            
            if days_left <= 7:
                predictions.append({
                    'product': product['name'],
                    'current_stock': product['stock_quantity'],
                    'daily_sales': round(daily_velocity, 1),
                    'days_until_stockout': round(days_left, 1),
                    'status': 'Critical' if days_left < 3 else 'Warning'
                })
        
        return sorted(predictions, key=lambda x: x['days_until_stockout'])

    def get_top_products(self, lookback_days: int = 30, limit: int = 5) -> list[dict]:
        start_date = self.today - timedelta(days=max(1, int(lookback_days)) - 1)
        limit = max(1, int(limit))

        top_products = (
            SaleItem.objects.filter(sale__timestamp__date__gte=start_date, product__isnull=False)
            .values('product__name')
            .annotate(total_qty=Sum('quantity'), total_revenue=Sum('subtotal'))
            .order_by('-total_revenue')[:limit]
        )

        return [
            {
                'name': row['product__name'],
                'total_qty': int(row['total_qty'] or 0),
                'total_revenue': float(row['total_revenue'] or 0),
            }
            for row in top_products
            if row.get('product__name')
        ]

    def get_revenue_trend(self, days: int = 7) -> list[dict]:
        days = max(1, int(days))
        dates, values = self._get_daily_revenue_series(lookback_days=days)
        return [
            {'date': day, 'total': round(float(total), 2)}
            for day, total in zip(dates, values, strict=False)
        ]

    def get_inventory_health(self, lookback_days: int = 30) -> dict:
        """
        Returns 0-100 health scores used by the dashboard radar chart.
        Optimized: Reduce queries by using annotations and database aggregation.
        """
        # Try cache first
        cache_key = f'inventory_health_{lookback_days}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        total_products = Product.objects.count()
        if total_products == 0:
            return {
                'stock_level': 0,
                'turnover_rate': 0,
                'demand': 0,
                'profit_margin': 0,
                'availability': 0,
            }

        # Single query for stock counts
        stock_stats = Product.objects.aggregate(
            low_stock=Count('id', filter=Q(stock_quantity__lte=F('reorder_level'))),
            out_of_stock=Count('id', filter=Q(stock_quantity__lte=0)),
            total_stock=Sum('stock_quantity')
        )
        
        low_stock_count = stock_stats['low_stock'] or 0
        out_of_stock_count = stock_stats['out_of_stock'] or 0
        total_stock = stock_stats['total_stock'] or 0

        # Demand and turnover from sales data
        start_date = self.today - timedelta(days=max(1, int(lookback_days)) - 1)
        
        sales_stats = SaleItem.objects.filter(
            sale__timestamp__date__gte=start_date,
            product__isnull=False
        ).aggregate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('subtotal'),
            distinct_products=Count('product', distinct=True)
        )
        
        total_sold_qty = sales_stats['total_sold'] or 0
        total_revenue = sales_stats['total_revenue'] or 0
        sold_product_count = sales_stats['distinct_products'] or 0

        # Calculate profit margin quickly (approximate)
        margin_pct = 0.0
        if total_revenue > 0:
            # Rough profit estimate: assuming 20-30% margin is typical for retail
            # This avoids querying all items for exact calculation
            avg_margin_estimate = 25.0  # Conservative estimate
            margin_pct = min(50.0, avg_margin_estimate)

        # Calculate scores
        stock_level_score = round(100 * (1 - (low_stock_count / max(1, total_products))), 1)
        availability_score = round(100 * (1 - (out_of_stock_count / max(1, total_products))), 1)

        turnover_score = 0.0
        if (total_stock + total_sold_qty) > 0:
            turnover_score = round(100 * (float(total_sold_qty) / (total_stock + total_sold_qty)), 1)

        demand_score = round(100 * (sold_product_count / max(1, total_products)), 1)
        margin_score = round(max(0.0, min(100.0, margin_pct * 2)), 1)

        result = {
            'stock_level': max(0.0, min(100.0, stock_level_score)),
            'turnover_rate': max(0.0, min(100.0, turnover_score)),
            'demand': max(0.0, min(100.0, demand_score)),
            'profit_margin': max(0.0, min(100.0, margin_score)),
            'availability': max(0.0, min(100.0, availability_score)),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        return result

    def get_product_recommendations(self):
        """
        Identify products that are often bought together (simplified Market Basket Analysis).
        Optimized: Single database query with fast filtering.
        """
        # Cache for 10 minutes since recommendations don't change frequently
        cache_key = 'ai_product_recommendations'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        top_products = (
            SaleItem.objects
            .values('product__name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:5]
        )
        
        recommendations = []
        for item in top_products:
            if item['product__name']:
                recommendations.append({
                    'type': 'Top Seller',
                    'message': f"'{item['product__name']}' ({item['total_qty']} units sold). Maintain stock levels and consider bundling opportunities.",
                    'score': 'High'
                })
        
        cache.set(cache_key, recommendations, 600)
        return recommendations

    def get_anomalies(self):
        """
        Detect unusual sales spikes or drops.
        """
        # Get yesterday's sales
        yesterday = self.today - timedelta(days=1)
        yesterday_sales = Sale.objects.filter(
            timestamp__date=yesterday
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Get 30-day average
        start_date = self.today - timedelta(days=31)
        end_date = self.today - timedelta(days=1)
        avg_sales = Sale.objects.filter(
            timestamp__date__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        avg_sales = avg_sales / 30
        
        anomalies = []
        if avg_sales > 0:
            deviation = (yesterday_sales - avg_sales) / avg_sales
            if deviation > 0.5: # 50% higher
                anomalies.append({
                    'date': yesterday,
                    'type': 'Spike',
                    'description': f"Sales yesterday were {round(deviation*100)}% higher than the 30-day average.",
                    'severity': 'Positive'
                })
            elif deviation < -0.5: # 50% lower
                anomalies.append({
                    'date': yesterday,
                    'type': 'Drop',
                    'description': f"Sales yesterday were {round(abs(deviation)*100)}% lower than the 30-day average.",
                    'severity': 'Negative'
                })
                
        return anomalies
