from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('categories/', views.category_list, name='inventory_category_list'),
    path('categories/add/', views.category_add, name='inventory_category_add'),
    path('categories/edit/<int:pk>/', views.category_edit, name='inventory_category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='inventory_category_delete'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),
    path('pdf/', views.inventory_pdf, name='inventory_pdf'),
]
