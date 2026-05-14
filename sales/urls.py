from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.pos_interface, name='pos'),
    path('api/search-product/', views.search_product, name='search_product'),
    path('api/process-sale/', views.process_sale, name='process_sale'),
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),
    path('sales/<int:pk>/pdf/', views.sale_receipt_pdf, name='sale_receipt_pdf'),
]
