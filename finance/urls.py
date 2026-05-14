from django.urls import path
from . import views

urlpatterns = [
    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/update/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/dashboard/', views.expense_dashboard, name='expense_dashboard'),
    path('expenses/pdf/', views.expense_list_pdf, name='expense_list_pdf'),
    # Finance overview and PDF
    path('overview/', views.finance_overview, name='finance_overview'),
    path('overview/pdf/', views.finance_overview, name='finance_overview_pdf'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
