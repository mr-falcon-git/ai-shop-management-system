from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('sales/pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('profit-loss/pdf/', views.profit_loss_pdf, name='profit_loss_pdf'),
]
