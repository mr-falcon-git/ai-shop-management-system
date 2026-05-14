from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import Product, Category, Supplier

@login_required
def product_list(request):
    products = Product.objects.select_related('category', 'supplier').all()
    low_stock_count = products.filter(stock_quantity__lte=models.F('reorder_level')).count()
    
    context = {
        'products': products,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        barcode = request.POST.get('barcode')
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        description = request.POST.get('description', '')
        unit = request.POST.get('unit', 'pcs')
        buy_price = request.POST.get('buy_price')
        sell_price = request.POST.get('sell_price')
        stock_quantity = request.POST.get('stock_quantity', 0)
        reorder_level = request.POST.get('reorder_level', 10)
        
        # Check for duplicate barcode
        if Product.objects.filter(barcode=barcode).exists():
            messages.error(request, f'Error: A product with barcode "{barcode}" already exists.')
            categories = Category.objects.all()
            suppliers = Supplier.objects.all()
            context = {
                'categories': categories,
                'suppliers': suppliers,
                'product': {
                    'name': name,
                    'barcode': barcode,
                    'category': {'id': int(category_id)} if category_id else None,
                    'category_id': int(category_id) if category_id else None,
                    'supplier': {'id': int(supplier_id)} if supplier_id else None,
                    'supplier_id': int(supplier_id) if supplier_id else None,
                    'description': description,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'stock_quantity': stock_quantity,
                    'reorder_level': reorder_level
                }
            }
            return render(request, 'inventory/product_form.html', context)
        
        try:
            category = Category.objects.get(id=category_id) if category_id else None
            supplier = Supplier.objects.get(id=supplier_id) if supplier_id else None
            
            Product.objects.create(
                name=name,
                barcode=barcode,
                category=category,
                supplier=supplier,
                description=description,
                unit=unit,
                buy_price=buy_price,
                sell_price=sell_price,
                stock_quantity=stock_quantity,
                reorder_level=reorder_level
            )
            messages.success(request, f'Product "{name}" added successfully!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    context = {
        'categories': categories,
        'suppliers': suppliers,
    }
    return render(request, 'inventory/product_form.html', context)

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.barcode = request.POST.get('barcode')
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        product.description = request.POST.get('description', '')
        product.unit = request.POST.get('unit', 'pcs')
        product.buy_price = request.POST.get('buy_price')
        product.sell_price = request.POST.get('sell_price')
        product.stock_quantity = request.POST.get('stock_quantity', 0)
        product.reorder_level = request.POST.get('reorder_level', 10)
        
        # Update foreign key IDs for the form context in case of error
        if category_id:
            product.category_id = int(category_id)
        else:
            product.category_id = None
            
        if supplier_id:
            product.supplier_id = int(supplier_id)
        else:
            product.supplier_id = None
        
        # Check for duplicate barcode
        if Product.objects.filter(barcode=product.barcode).exclude(pk=pk).exists():
            messages.error(request, f'Error: A product with barcode "{product.barcode}" already exists.')
            categories = Category.objects.all()
            suppliers = Supplier.objects.all()
            context = {
                'product': product,
                'categories': categories,
                'suppliers': suppliers,
            }
            return render(request, 'inventory/product_form.html', context)
        
        try:
            product.category = Category.objects.get(id=category_id) if category_id else None
            product.supplier = Supplier.objects.get(id=supplier_id) if supplier_id else None
            product.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    context = {
        'product': product,
        'categories': categories,
        'suppliers': suppliers,
    }
    return render(request, 'inventory/product_form.html', context)

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted successfully!')
        return redirect('product_list')
    
    context = {'product': product}
    return render(request, 'inventory/product_confirm_delete.html', context)

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Category "{name}" already exists.')
        else:
            try:
                Category.objects.create(name=name, description=description)
                messages.success(request, f'Category "{name}" added successfully!')
                return redirect('inventory_category_list')
            except Exception as e:
                messages.error(request, f'Error adding category: {str(e)}')

    return render(request, 'inventory/category_form.html')

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Category "{name}" already exists.')
        else:
            try:
                category.name = name
                category.description = description
                category.save()
                messages.success(request, f'Category "{category.name}" updated successfully!')
                return redirect('inventory_category_list')
            except Exception as e:
                messages.error(request, f'Error updating category: {str(e)}')

    return render(request, 'inventory/category_form.html', {'category': category})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('inventory_category_list')

    return render(request, 'inventory/category_confirm_delete.html', {'category': category})

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not name or not phone:
            messages.error(request, 'Supplier name and phone are required.')
        else:
            try:
                Supplier.objects.create(
                    name=name,
                    contact_person=contact_person,
                    email=email,
                    phone=phone,
                    address=address
                )
                messages.success(request, f'Supplier "{name}" added successfully!')
                return redirect('supplier_list')
            except Exception as e:
                messages.error(request, f'Error adding supplier: {str(e)}')

    return render(request, 'inventory/supplier_form.html')

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.name = request.POST.get('name', '').strip()
        supplier.contact_person = request.POST.get('contact_person', '').strip()
        supplier.email = request.POST.get('email', '').strip()
        supplier.phone = request.POST.get('phone', '').strip()
        supplier.address = request.POST.get('address', '').strip()

        if not supplier.name or not supplier.phone:
            messages.error(request, 'Supplier name and phone are required.')
        else:
            try:
                supplier.save()
                messages.success(request, f'Supplier "{supplier.name}" updated successfully!')
                return redirect('supplier_list')
            except Exception as e:
                messages.error(request, f'Error updating supplier: {str(e)}')

    return render(request, 'inventory/supplier_form.html', {'supplier': supplier})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier "{name}" deleted successfully!')
        return redirect('supplier_list')

    return render(request, 'inventory/supplier_confirm_delete.html', {'supplier': supplier})

@login_required
def inventory_pdf(request):
    """Generate PDF report of inventory"""
    from shop_system.utils import render_to_pdf
    from django.http import HttpResponse
    from django.utils import timezone
    from django.db.models import F
    
    products = Product.objects.select_related('category').all().order_by('name')
    
    # Calculate stats
    total_products = products.count()
    low_stock_products = products.filter(stock_quantity__lte=F('reorder_level')).count()
    out_of_stock = products.filter(stock_quantity=0).count()
    
    # Calculate total value and add stock_value to each product
    total_value = 0
    for product in products:
        product.stock_value = product.stock_quantity * product.buy_price
        total_value += product.stock_value
        
    context = {
        'products': products,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'total_value': total_value,
        'now': timezone.now(),
        'generated_by': request.user.username
    }
    
    pdf = render_to_pdf('inventory/inventory_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Inventory_Report_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error Rendering PDF", status=400)
