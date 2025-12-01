from django.urls import path
from . import views

urlpatterns = [
    # Сторінка, де користувач починає оплату
    path('pay/', views.initiate_payment_view, name='initiate_payment'),

    # URL, який ви вказуєте в налаштуваннях LiqPay (server_url)
    path('liqpay-callback/', views.liqpay_callback_view, name='liqpay_callback'),

    # URL, куди перенаправить користувача після оплати (result_url)
    path('payment-success/', views.payment_success_view, name='payment_success'),
]
