from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Sale, SaleItem
from inventory.models import Product
import json
from decimal import Decimal

@login_required
def pos_interface(request):
    """Point of Sale interface"""
    products = Product.objects.filter(stock_quantity__gt=0).select_related('category')
    return render(request, 'sales/pos.html', {'products': products})

@login_required
def search_product(request):
    """AJAX endpoint to search products by barcode or name"""
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            Q(barcode__icontains=query) | Q(name__icontains=query),
            stock_quantity__gt=0
        ).values('id', 'name', 'barcode', 'sell_price', 'stock_quantity')[:10]
        
        return JsonResponse(list(products), safe=False)
    
    return JsonResponse([], safe=False)

@login_required
@require_POST
def process_sale(request):
    """Process a sale transaction"""
    try:
        data = json.loads((request.body or b'{}').decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    raw_items = data.get('items') or []
    payment_method = (data.get('payment_method') or 'cash').strip().lower()

    allowed_payment_methods = {key for key, _label in Sale.PAYMENT_METHODS}
    if payment_method not in allowed_payment_methods:
        return JsonResponse({'success': False, 'error': 'Invalid payment method'}, status=400)

    if not isinstance(raw_items, list) or not raw_items:
        return JsonResponse({'success': False, 'error': 'No items in cart'}, status=400)

    # Aggregate duplicate products from the UI into a single quantity per product.
    aggregated_items: dict[int, int] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            return JsonResponse({'success': False, 'error': 'Invalid cart item'}, status=400)

        product_id = raw_item.get('product_id')
        quantity = raw_item.get('quantity')
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid product_id or quantity'}, status=400)

        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'}, status=400)

        aggregated_items[product_id] = aggregated_items.get(product_id, 0) + quantity

    if not aggregated_items:
        return JsonResponse({'success': False, 'error': 'No items in cart'}, status=400)

    try:
        with transaction.atomic():
            sale = Sale.objects.create(
                cashier=request.user,
                payment_method=payment_method,
                total_amount=Decimal('0.00'),
            )

            total = Decimal('0.00')

            for product_id, quantity in aggregated_items.items():
                product = Product.objects.select_for_update().get(id=product_id)

                if product.stock_quantity < quantity:
                    raise ValueError(f'Insufficient stock for {product.name}')

                line_subtotal = Decimal(quantity) * product.sell_price

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price_at_sale=product.sell_price,
                    subtotal=line_subtotal,
                )

                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])

                total += line_subtotal

            sale.total_amount = total
            sale.save(update_fields=['total_amount'])

        return JsonResponse({'success': True, 'sale_id': sale.id, 'total': float(total)})

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Could not process sale'}, status=500)

@login_required
def sales_list(request):
    """List all sales"""
    sales = Sale.objects.select_related('cashier').prefetch_related('items__product').order_by('-timestamp')
    
    # Calculate statistics
    from django.db.models import Sum, Avg
    total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    average_sale = sales.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    
    context = {
        'sales': sales,
        'total_revenue': total_revenue,
        'average_sale': average_sale,
    }
    return render(request, 'sales/sales_list.html', context)

@login_required
def sale_detail(request, pk):
    """View sale details"""
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})

@login_required
def sale_delete(request, pk):
    """Delete a sale and return sold quantities to stock."""
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            for item in sale.items.select_related('product'):
                if item.product_id:
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    product.stock_quantity += item.quantity
                    product.save(update_fields=['stock_quantity'])

            sale_id = sale.id
            sale.delete()

        messages.success(request, f'Sale #{sale_id} deleted and stock restored successfully!')
        return redirect('sales_list')

    return render(request, 'sales/sale_confirm_delete.html', {'sale': sale})

@login_required
def sale_receipt_pdf(request, pk):
    """Generate PDF receipt for a sale"""
    from shop_system.utils import render_to_pdf
    from django.http import HttpResponse
    
    sale = get_object_or_404(Sale.objects.prefetch_related('items__product'), pk=pk)
    
    context = {
        'sale': sale,
    }
    
    pdf = render_to_pdf('sales/receipt_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Receipt_SALE-{sale.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Rendering PDF", status=400)
