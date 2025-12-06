import logging
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import StudioPayment
from .services import LiqPayService, CheckboxService
from .tasks import retry_checkbox_receipt

# Configure logging
logger = logging.getLogger(__name__)


@csrf_exempt
def initiate_payment_view(request: HttpRequest) -> HttpResponse:
    """
    Сторінка, де користувач ініціює оплату.
    У реальному додатку тут буде форма з вибором послуги, дати тощо.
    """
    if request.method == 'POST':
        try:
            # Для прикладу, створюємо платіж на фіксовану суму
            # У реальному додатку сума має надходити з форми
            amount_to_pay = Decimal('500.00')

            payment = StudioPayment.objects.create(
                amount=amount_to_pay,
                description=f"Передоплата за оренду студії (приклад)"
            )

            logger.info(f"Payment {payment.id} created for amount {amount_to_pay} UAH")

            # Генеруємо дані для форми LiqPay
            liqpay = LiqPayService()
            form_data = liqpay.generate_payment_form(payment)

            # Рендеримо сторінку, яка автоматично відправить користувача на LiqPay
            return render(request, 'payment_service/process_payment.html', form_data)

        except Exception as e:
            logger.error(f"Error initiating payment: {e}", exc_info=True)
            return HttpResponse("Помилка при створенні платежу", status=500)

    # GET-запит - просто показуємо кнопку "Оплатити"
    return render(request, 'payment_service/initiate_payment.html')


@csrf_exempt
@transaction.atomic
def liqpay_callback_view(request: HttpRequest) -> HttpResponse:
    """
    View для `server_url` LiqPay.
    Отримує POST-запит від LiqPay про статус платежу.
    """
    if request.method != 'POST':
        logger.warning("LiqPay callback received non-POST request")
        return HttpResponse(status=405)  # Method Not Allowed

    data = request.POST.get('data')
    signature = request.POST.get('signature')

    if not data or not signature:
        logger.warning("LiqPay callback missing data or signature")
        return HttpResponse(status=400)  # Bad Request

    liqpay = LiqPayService()

    # 1. Верифікуємо підпис
    decoded_data = liqpay.verify_callback(data, signature)

    if not decoded_data:
        logger.error("LiqPay callback signature verification failed")
        return HttpResponse(status=400)  # Bad Request (invalid signature)

    order_id = decoded_data.get('order_id')
    status = decoded_data.get('status')
    amount = decoded_data.get('amount')

    logger.info(
        f"LiqPay callback received: order_id={order_id}, "
        f"status={status}, amount={amount}"
    )

    try:
        # Використовуємо select_for_update для запобігання race conditions
        payment = StudioPayment.objects.select_for_update().get(id=order_id)
    except StudioPayment.DoesNotExist:
        logger.error(
            f"Payment {order_id} not found in database. "
            "Possible fraud attempt or external order_id"
        )
        return HttpResponse(status=404)  # Not Found

    # Перевіряємо, чи сума збігається (захист від підміни)
    if str(payment.amount) != str(amount):
        logger.critical(
            f"Amount mismatch for payment {order_id}! "
            f"Expected: {payment.amount}, Got: {amount}"
        )
        return HttpResponse(status=400)

    payment.liqpay_status = status

    # 2. Перевіряємо статус платежу
    # 'sandbox' - для тестових платежів, 'success' - для реальних
    is_successful_payment = status in ('success', 'sandbox')

    # Обробляємо платіж, лише якщо він успішний І ми ще не обробили його
    if is_successful_payment and not payment.is_paid:
        payment.is_paid = True
        payment.save()

        logger.info(f"Payment {payment.id} marked as paid")

        # 3. Створюємо фіскальний чек в Checkbox
        checkbox = CheckboxService()
        # В ідеалі, тут треба передати email клієнта, якщо він у вас є
        # Можна отримати з decoded_data або з моделі користувача
        client_email = decoded_data.get('sender_email', 'client_email@example.com')
        receipt_data = checkbox.create_receipt(payment, client_email=client_email)

        if receipt_data:
            # 4. Зберігаємо дані про чек
            payment.checkbox_receipt_id = receipt_data.get('id')
            payment.checkbox_fiscal_code = receipt_data.get('fiscal_code')
            payment.checkbox_status = receipt_data.get('status')
            payment.save()

            logger.info(
                f"Checkbox receipt created for payment {payment.id}: "
                f"receipt_id={payment.checkbox_receipt_id}"
            )
        else:
            # КРИТИЧНО! Оплата пройшла, але чек не створився.
            logger.critical(
                f"CRITICAL: Payment {payment.id} paid but Checkbox receipt failed! "
                "Adding to retry queue."
            )

            # Додаємо завдання на повторну спробу через Celery
            # Якщо Celery не налаштований, закоментуйте цей рядок
            try:
                retry_checkbox_receipt.apply_async(
                    args=[str(payment.id)],
                    countdown=300  # Повторна спроба через 5 хвилин
                )
            except Exception as e:
                logger.error(
                    f"Failed to queue retry task for payment {payment.id}: {e}",
                    exc_info=True
                )

    elif not is_successful_payment:
        # Обробка неуспішних статусів (failure, reversed тощо)
        payment.is_paid = False
        payment.save()

        logger.warning(
            f"Payment {payment.id} failed with status: {status}"
        )

    # LiqPay очікує відповідь 200 OK
    return HttpResponse(status=200)


@csrf_exempt
def payment_success_view(request: HttpRequest) -> HttpResponse:
    """
    Сторінка `result_url`, куди LiqPay перенаправить користувача
    після оплати.
    """
    # Отримуємо дані від LiqPay
    data = request.POST.get('data') or request.GET.get('data')
    signature = request.POST.get('signature') or request.GET.get('signature')

    payment = None

    if data and signature:
        liqpay = LiqPayService()
        decoded_data = liqpay.verify_callback(data, signature)

        if decoded_data:
            order_id = decoded_data.get('order_id')
            try:
                payment = StudioPayment.objects.get(id=order_id)
                logger.info(f"User returned to success page for payment {order_id}")
            except StudioPayment.DoesNotExist:
                logger.error(f"Payment {order_id} not found on success page")

    return render(request, 'payment_service/payment_success.html', {
        'payment': payment
    })