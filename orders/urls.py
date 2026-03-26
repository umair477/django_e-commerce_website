from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('invoice/<str:order_number>/', views.invoice, name='order_invoice'),
    path('detail/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('reorder/<int:order_id>/', views.reorder, name='reorder_order'),
]
