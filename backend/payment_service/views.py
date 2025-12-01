from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import StudioPayment
from .services import LiqPayService, CheckboxService
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView

@csrf_exempt
def initiate_payment_view(request: HttpRequest) -> HttpResponse:
    """
    Сторінка, де користувач ініціює оплату.
    У реальному додатку тут буде форма з вибором послуги, дати тощо.
    """
    if request.method == 'POST':
        # Для прикладу, створюємо платіж на фіксовану суму
        # У реальному додатку сума має надходити з форми
        amount_to_pay = Decimal('500.00')

        payment = StudioPayment.objects.create(
            amount=amount_to_pay,
            description=f"Передоплата за оренду студії (приклад)"
        )

        # 1. Генеруємо дані для форми LiqPay
        liqpay = LiqPayService()
        form_data = liqpay.generate_payment_form(payment)

        # 2. Рендеримо сторінку, яка автоматично відправить користувача на LiqPay
        return render(request, 'payment_service/process_payment.html', form_data)

    # GET-запит - просто показуємо кнопку "Оплатити"
    return render(request, 'payment_service/initiate_payment.html')


@csrf_exempt
def liqpay_callback_view(request: HttpRequest) -> HttpResponse:
    """
    View для `server_url` LiqPay.
    Отримує POST-запит від LiqPay про статус платежу.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed

    data = request.POST.get('data')
    signature = request.POST.get('signature')

    if not data or not signature:
        return HttpResponse(status=400)  # Bad Request

    liqpay = LiqPayService()

    # 1. Верифікуємо підпис
    decoded_data = liqpay.verify_callback(data, signature)

    if not decoded_data:
        # TODO: Логувати спробу підробки запиту
        return HttpResponse(status=400)  # Bad Request (invalid signature)

    order_id = decoded_data.get('order_id')
    status = decoded_data.get('status')

    try:
        payment = StudioPayment.objects.get(id=order_id)
    except StudioPayment.DoesNotExist:
        # TODO: Логувати! Можливо, платіж не з нашої системи
        return HttpResponse(status=404)  # Not Found

    payment.liqpay_status = status

    # 2. Перевіряємо статус платежу
    # 'sandbox' - для тестових платежів, 'success' - для реальних
    is_successful_payment = status in ('success', 'sandbox')

    # Обробляємо платіж, лише якщо він успішний І ми ще не обробили його
    if is_successful_payment and not payment.is_paid:
        payment.is_paid = True
        payment.save()

        # 3. Створюємо фіскальний чек в Checkbox
        checkbox = CheckboxService()
        # В ідеалі, тут треба передати email клієнта, якщо він у вас є
        receipt_data = checkbox.create_receipt(payment, client_email="client_email@example.com")

        if receipt_data:
            # 4. Зберігаємо дані про чек
            payment.checkbox_receipt_id = receipt_data.get('id')
            payment.checkbox_fiscal_code = receipt_data.get('fiscal_code')
            payment.checkbox_status = receipt_data.get('status')
            payment.save()
        else:
            # КРИТИЧНО! Оплата пройшла, але чек не створився.
            # TODO: Потрібно додати механізм повторної фіскалізації!
            # (напр. Celery task або cron)
            print(f"CRITICAL: Payment {payment.id} paid but Checkbox receipt failed!")

    elif not is_successful_payment:
        # Обробка неуспішних статусів (failure, reversed тощо)
        payment.is_paid = False
        payment.save()

    # LiqPay очікує відповідь 200 OK, щоб зрозуміти, що ми отримали callback
    return HttpResponse(status=200)

@csrf_exempt
def payment_success_view(request: HttpRequest) -> HttpResponse:
    """
    Сторінка `result_url`, куди LiqPay перенаправить користувача
    після оплати.
    """
    # Тут можна отримати order_id з POST/GET даних від LiqPay
    # і показати користувачу деталі замовлення.
    # Для простоти - просто показуємо "успіх".
    return render(request, 'payment_service/payment_success.html')
