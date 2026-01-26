import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.cache import cache
from .models import StudioPayment
from .services import LiqPayService, CheckboxService

logger = logging.getLogger(__name__)


@csrf_exempt
def initiate_payment_view(request: HttpRequest) -> HttpResponse:
    """Сторінка, де користувач ініціює оплату."""
    if request.method == 'POST':
        try:
            amount_to_pay = Decimal('500.00')
            payment = StudioPayment.objects.create(
                amount=amount_to_pay,
                description=f"Передоплата за оренду студії (приклад)"
            )
            logger.info(f"Payment {payment.id} created for amount {amount_to_pay} UAH")

            liqpay = LiqPayService()
            form_data = liqpay.generate_payment_form(payment, request.build_absolute_uri('/')[:-1])
            return render(request, 'payment_service/process_payment.html', form_data)
        except Exception as e:
            logger.error(f"Error initiating payment: {e}", exc_info=True)
            return HttpResponse("Помилка при створенні платежу", status=500)

    return render(request, 'payment_service/initiate_payment.html')


@csrf_exempt
@transaction.atomic
def liqpay_callback_view(request: HttpRequest) -> HttpResponse:
    """View для server_url LiqPay - основний callback."""
    logger.info("=" * 80)
    logger.info("=== LIQPAY SERVER CALLBACK RECEIVED ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"POST data: {request.POST}")
    logger.info(f"GET data: {request.GET}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info("=" * 80)

    if request.method != 'POST':
        logger.warning("LiqPay callback received non-POST request")
        return HttpResponse(status=405)

    data = request.POST.get('data')
    signature = request.POST.get('signature')

    if not data or not signature:
        logger.error("❌ LiqPay callback missing data or signature")
        return HttpResponse(status=400)

    logger.info(f"Data received: {data[:100]}...")
    logger.info(f"Signature received: {signature}")

    return process_liqpay_payment(data, signature)


@csrf_exempt
def payment_success_view(request: HttpRequest) -> HttpResponse:
    logger.info("=" * 80)
    logger.info("=== PAYMENT SUCCESS VIEW CALLED ===")

    # 1. Витягуємо ID (шукаємо скрізь)
    order_id = (
            request.GET.get('order_id') or
            request.POST.get('order_id') or
            request.GET.get('payment_id') or
            request.POST.get('payment_id')
    )

    # LiqPay іноді повертає data/signature і в GET запиті (залежить від налаштувань)
    data = request.POST.get('data') or request.GET.get('data')
    signature = request.POST.get('signature') or request.GET.get('signature')

    if not order_id and data and signature:
        # Спробуємо розшифрувати data, щоб дістати order_id
        try:
            liqpay = LiqPayService()
            decoded = liqpay.verify_callback(data, signature)
            if decoded:
                order_id = decoded.get('order_id')
                logger.info(f"Extracted order_id from data: {order_id}")
        except Exception as e:
            logger.error(f"Failed to decode data in success view: {e}")

    if not order_id:
        logger.warning("⚠️ No order_id found! Redirecting to home.")
        return redirect('/')

    logger.info(f"Processing return for Payment ID: {order_id}")

    # 2. Логіка примусової перевірки
    try:
        payment = StudioPayment.objects.get(id=order_id)

        # Якщо у нас в базі ще не "Paid", стукаємо в LiqPay API прямо зараз
        if not payment.is_paid:
            logger.info(f"Payment {order_id} is pending locally. Force checking API...")

            liqpay_service = LiqPayService()
            api_response = liqpay_service.check_payment_status(str(order_id))

            if api_response:
                api_status = api_response.get('status')
                logger.info(f"LiqPay API returned status: {api_status}")

                # Список успішних статусів LiqPay
                if api_status in ('success', 'sandbox', 'wait_accept'):
                    # Оновлюємо ПЛАТІЖ
                    payment.is_paid = True
                    payment.liqpay_status = api_status
                    payment.save(update_fields=['is_paid', 'liqpay_status'])

                    # Оновлюємо БРОНЮВАННЯ
                    if hasattr(payment, 'booking') and payment.booking:
                        booking = payment.booking
                        if booking.status == 'pending_payment':
                            booking.status = 'paid'
                            booking.save(update_fields=['status'])
                            logger.info(f"✅ Booking {booking.id} auto-updated to PAID via Force Check")
                else:
                    # Оновлюємо статус (наприклад, failure), але не is_paid
                    payment.liqpay_status = api_status
                    payment.save(update_fields=['liqpay_status'])

    except StudioPayment.DoesNotExist:
        logger.error(f"❌ Payment {order_id} not found in DB")
    except Exception as e:
        logger.error(f"❌ Error in force check: {e}", exc_info=True)

    # 3. Редірект на фронтенд з ID
    logger.info(f"Redirecting user to frontend: /payment/success?payment_id={order_id}")
    return redirect(f'/payment/success?payment_id={order_id}')


def process_liqpay_payment(data: str, signature: str) -> HttpResponse:
    """Обробка платежу LiqPay з захистом від race conditions."""
    logger.info("--- PROCESSING LIQPAY PAYMENT ---")

    liqpay = LiqPayService()
    decoded_data = liqpay.verify_callback(data, signature)

    if not decoded_data:
        logger.error("❌ LiqPay signature verification FAILED")
        return HttpResponse(status=400)

    logger.info(f"✅ Signature verified. Decoded data: {decoded_data}")

    order_id = decoded_data.get('order_id')
    status = decoded_data.get('status')
    amount = decoded_data.get('amount')

    logger.info(f"Order ID: {order_id}")
    logger.info(f"Status: {status}")
    logger.info(f"Amount: {amount}")

    # 🔒 КРИТИЧНО: Використовуємо distributed lock для запобігання race condition
    lock_key = f"payment_processing_{order_id}"
    lock_acquired = cache.add(lock_key, "locked", timeout=30)  # 30 секунд

    if not lock_acquired:
        logger.warning(f"⚠️ Payment {order_id} is already being processed by another request")
        return HttpResponse(status=200)  # OK, але не обробляємо

    try:
        with transaction.atomic():
            # 🔒 Блокуємо рядок в БД
            payment = StudioPayment.objects.select_for_update(nowait=False).get(id=order_id)

            logger.info(
                f"Found payment {payment.id}, current status: is_paid={payment.is_paid}, "
                f"liqpay_status={payment.liqpay_status}"
            )

            # 🔒 Перевірка чи вже оброблено (після блокування!)
            if payment.is_paid and payment.liqpay_status in ('success', 'sandbox'):
                logger.info(f"ℹ️ Payment {payment.id} already processed successfully, skipping")
                return HttpResponse(status=200)

            # 🔒 КРИТИЧНО: Валідація суми
            expected_amount = Decimal(str(payment.amount))
            received_amount = Decimal(str(amount))

            if expected_amount != received_amount:
                logger.critical(
                    f"🚨 SECURITY ALERT: Amount mismatch for payment {payment.id}! "
                    f"Expected: {expected_amount} UAH, Received: {received_amount} UAH"
                )
                payment.liqpay_status = 'fraud_suspected'
                payment.save(update_fields=['liqpay_status'])

                # Надсилаємо алерт (додайте свою логіку)
                # send_security_alert(payment, expected_amount, received_amount)

                return HttpResponse("Amount mismatch detected", status=400)

            # Оновлюємо статус
            old_status = payment.liqpay_status
            payment.liqpay_status = status

            logger.info(f"Updating LiqPay status: {old_status} → {status}")

            is_successful = status in ('success', 'sandbox')

            if is_successful and not payment.is_paid:
                payment.is_paid = True
                payment.save()
                logger.info(f"✅✅✅ Payment {payment.id} marked as PAID ✅✅✅")

                # Оновлюємо бронювання
                try:
                    if hasattr(payment, 'booking') and payment.booking:
                        from bookings.models import StudioBooking
                        booking = StudioBooking.objects.select_for_update().get(id=payment.booking.id)

                        old_booking_status = booking.status
                        logger.info(f"Found booking {booking.id}, current status: {old_booking_status}")

                        if booking.status == 'pending_payment':
                            booking.status = 'paid'
                            booking.save(update_fields=['status'])
                            logger.info(
                                f"✅✅✅ Booking {booking.id} updated: {old_booking_status} → paid ✅✅✅"
                            )
                        else:
                            logger.info(f"ℹ️ Booking {booking.id} already in status '{booking.status}'")
                    else:
                        logger.warning(f"⚠️ Payment {payment.id} has NO associated booking")
                except Exception as e:
                    logger.error(f"❌❌❌ FAILED to update booking: {e}", exc_info=True)

                # Checkbox - тільки якщо є email
                try_create_checkbox_receipt(payment, decoded_data)

            elif not is_successful:
                payment.is_paid = False
                payment.save()
                logger.warning(f"❌ Payment {payment.id} FAILED with status: {status}")

                # Скасовуємо бронювання
                try:
                    if hasattr(payment, 'booking') and payment.booking:
                        booking = payment.booking
                        if booking.status == 'pending_payment':
                            booking.status = 'cancelled'
                            booking.admin_notes += f"\nPayment failed: {status}"
                            booking.save(update_fields=['status', 'admin_notes'])
                            logger.info(f"Booking {booking.id} cancelled")
                except Exception as e:
                    logger.error(f"Failed to cancel booking: {e}")

            logger.info("--- PAYMENT PROCESSING COMPLETE ---")
            return HttpResponse(status=200)

    except StudioPayment.DoesNotExist:
        logger.error(f"❌ Payment {order_id} NOT FOUND in database")
        return HttpResponse(status=404)
    finally:
        # Завжди звільняємо lock
        cache.delete(lock_key)


@csrf_exempt
@transaction.atomic
def check_payment_status_api(request: HttpRequest, payment_id: str) -> JsonResponse:
    """API для перевірки статусу платежу з фронтенду."""
    logger.info("=" * 80)
    logger.info(f"=== FRONTEND CHECKING PAYMENT STATUS: {payment_id} ===")

    # 🔒 Rate limiting через cache
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_key = f"payment_check_rate_{client_ip}_{payment_id}"

    request_count = cache.get(rate_limit_key, 0)
    if request_count > 10:  # Максимум 10 запитів на хвилину
        logger.warning(f"⚠️ Rate limit exceeded for {client_ip} checking payment {payment_id}")
        return JsonResponse({
            'success': False,
            'error': 'Too many requests. Please wait.'
        }, status=429)

    cache.set(rate_limit_key, request_count + 1, 60)  # TTL 1 хвилина

    try:
        payment = StudioPayment.objects.get(id=payment_id)
        logger.info(f"Payment found: is_paid={payment.is_paid}, liqpay_status={payment.liqpay_status}")

        # Якщо не оплачений, перевіряємо через API
        if not payment.is_paid:
            logger.info("Payment not marked as paid, checking LiqPay API...")

            liqpay_service = LiqPayService()
            liqpay_status = liqpay_service.check_payment_status(payment_id)

            if liqpay_status:
                logger.info(f"LiqPay API response: {liqpay_status}")

                api_status = liqpay_status.get('status')
                api_amount = liqpay_status.get('amount')

                # 🔒 КРИТИЧНО: Перевірка суми з API
                if api_amount:
                    expected_amount = Decimal(str(payment.amount))
                    received_amount = Decimal(str(api_amount))

                    if expected_amount != received_amount:
                        logger.critical(
                            f"🚨 Amount mismatch in API check for payment {payment_id}! "
                            f"Expected: {expected_amount}, Got: {received_amount}"
                        )
                        return JsonResponse({
                            'success': False,
                            'error': 'Payment amount mismatch'
                        }, status=400)

                if api_status in ('success', 'sandbox'):
                    payment.is_paid = True
                    payment.liqpay_status = api_status
                    payment.save()
                    logger.info(f"✅✅✅ Payment {payment_id} updated to PAID via API ✅✅✅")

                    # Оновлюємо бронювання
                    if hasattr(payment, 'booking') and payment.booking:
                        from bookings.models import StudioBooking
                        booking = StudioBooking.objects.select_for_update().get(id=payment.booking.id)

                        if booking.status == 'pending_payment':
                            booking.status = 'paid'
                            booking.save(update_fields=['status'])
                            logger.info(f"✅✅✅ Booking {booking.id} updated to 'paid' via API ✅✅✅")
                else:
                    payment.liqpay_status = api_status
                    payment.save()
                    logger.info(f"Payment status from API: {api_status}")
            else:
                logger.warning("⚠️ Could not get status from LiqPay API")
        else:
            logger.info("✅ Payment already marked as paid")

        # Формуємо відповідь
        booking_info = None
        if hasattr(payment, 'booking') and payment.booking:
            booking = payment.booking
            booking_info = {
                'id': str(booking.id),
                'status': booking.status,
                'first_name': booking.first_name,
                'last_name': booking.last_name,
                'booking_date': booking.booking_date.isoformat(),
                'booking_time': booking.booking_time.strftime('%H:%M'),
            }

        response_data = {
            'success': True,
            'payment': {
                'id': str(payment.id),
                'amount': str(payment.amount),
                'is_paid': payment.is_paid,
                'liqpay_status': payment.liqpay_status,
            },
            'booking': booking_info
        }

        logger.info(f"Returning response: {response_data}")
        logger.info("=" * 80)
        return JsonResponse(response_data)

    except StudioPayment.DoesNotExist:
        logger.error(f"❌ Payment {payment_id} not found")
        return JsonResponse({'success': False, 'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def try_create_checkbox_receipt(payment: StudioPayment, decoded_data: dict):
    """Спроба створити чек Checkbox."""
    try:
        checkbox = CheckboxService()

        # 🔒 КРИТИЧНО: Отримуємо реальний email
        client_email = None

        if hasattr(payment, 'booking') and payment.booking and payment.booking.email:
            client_email = payment.booking.email
        elif decoded_data.get('sender_email'):
            client_email = decoded_data.get('sender_email')

        if not client_email:
            logger.warning(
                f"⚠️ No email available for payment {payment.id}, skipping Checkbox receipt"
            )
            return

        receipt_data = checkbox.create_receipt(payment, client_email=client_email)

        if receipt_data:
            payment.checkbox_receipt_id = receipt_data.get('id')
            payment.checkbox_fiscal_code = receipt_data.get('fiscal_code')
            payment.checkbox_status = receipt_data.get('status')
            payment.save(update_fields=[
                'checkbox_receipt_id',
                'checkbox_fiscal_code',
                'checkbox_status'
            ])
            logger.info(f"✅ Checkbox receipt created: {payment.checkbox_receipt_id}")
        else:
            logger.warning(f"⚠️ Checkbox receipt creation returned None for payment {payment.id}")

    except Exception as e:
        logger.error(f"❌ Checkbox error for payment {payment.id}: {e}", exc_info=True)