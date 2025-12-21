from django.contrib import admin
from django.utils.html import format_html
from .models import StudioPayment


@admin.register(StudioPayment)
class StudioPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id_short',
        'amount',
        'payment_status_badge',
        'liqpay_status_badge',
        'checkbox_status',
        'related_booking_link',
        'created_at'
    ]

    list_filter = [
        'is_paid',
        'liqpay_status',
        'checkbox_status',
        'created_at'
    ]

    search_fields = [
        'id',
        'description',
        'checkbox_receipt_id',
        'checkbox_fiscal_code'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'related_booking_link',
        'liqpay_details',
        'checkbox_details'
    ]

    fieldsets = (
        ('Основна інформація', {
            'fields': (
                'id',
                'amount',
                'description',
                'is_paid',
            )
        }),
        ('Пов\'язане бронювання', {
            'fields': (
                'related_booking_link',
            )
        }),
        ('LiqPay', {
            'fields': (
                'liqpay_status',
                'liqpay_details',
            )
        }),
        ('Checkbox (фіскалізація)', {
            'fields': (
                'checkbox_receipt_id',
                'checkbox_fiscal_code',
                'checkbox_status',
                'checkbox_details',
            )
        }),
        ('Системна інформація', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8]

    id_short.short_description = 'ID'

    def payment_status_badge(self, obj):
        if obj.is_paid:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ Оплачено</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #FFA500; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⏳ Очікується</span>'
            )

    payment_status_badge.short_description = 'Статус оплати'

    def liqpay_status_badge(self, obj):
        if not obj.liqpay_status:
            return '-'

        colors = {
            'success': '#4CAF50',
            'sandbox': '#2196F3',
            'failure': '#F44336',
            'error': '#F44336',
            'processing': '#FFA500',
        }
        color = colors.get(obj.liqpay_status, '#9E9E9E')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.liqpay_status.upper()
        )

    liqpay_status_badge.short_description = 'LiqPay статус'

    def related_booking_link(self, obj):
        try:
            if hasattr(obj, 'booking') and obj.booking:
                booking = obj.booking
                url = f'/admin/bookings/studiobooking/{booking.id}/change/'
                return format_html(
                    '<a href="{}" target="_blank">Бронювання {} - {} {}</a>',
                    url,
                    str(booking.id)[:8],
                    booking.first_name,
                    booking.last_name
                )
        except Exception:
            pass
        return format_html('<span style="color: #999;">Немає пов\'язаного бронювання</span>')

    related_booking_link.short_description = 'Пов\'язане бронювання'

    def liqpay_details(self, obj):
        if obj.liqpay_status:
            return format_html(
                '<div style="font-family: monospace;">'
                '<strong>Статус:</strong> {}<br>'
                '<strong>Оплачено:</strong> {}'
                '</div>',
                obj.liqpay_status,
                '✓ Так' if obj.is_paid else '✗ Ні'
            )
        return 'Дані відсутні'

    liqpay_details.short_description = 'Деталі LiqPay'

    def checkbox_details(self, obj):
        if obj.checkbox_receipt_id:
            return format_html(
                '<div style="font-family: monospace;">'
                '<strong>ID чека:</strong> {}<br>'
                '<strong>Фіскальний код:</strong> {}<br>'
                '<strong>Статус:</strong> {}'
                '</div>',
                obj.checkbox_receipt_id or '-',
                obj.checkbox_fiscal_code or '-',
                obj.checkbox_status or '-'
            )
        return 'Чек не створено'

    checkbox_details.short_description = 'Деталі Checkbox'

    actions = ['mark_as_paid', 'mark_as_unpaid']

    @admin.action(description='Позначити як оплачені')
    def mark_as_paid(self, request, queryset):
        updated = 0
        for payment in queryset.filter(is_paid=False):
            payment.is_paid = True
            payment.liqpay_status = 'success'
            payment.save()

            # Оновлюємо пов'язане бронювання
            try:
                if hasattr(payment, 'booking') and payment.booking:
                    booking = payment.booking
                    if booking.status == 'pending_payment':
                        booking.status = 'paid'
                        booking.save(update_fields=['status'])
            except Exception as e:
                self.message_user(request, f'Помилка оновлення бронювання: {e}', level='warning')

            updated += 1

        self.message_user(request, f'{updated} платежів позначено як оплачені')

    @admin.action(description='Позначити як неоплачені')
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.filter(is_paid=True).update(is_paid=False)
        self.message_user(request, f'{updated} платежів позначено як неоплачені')

    def save_model(self, request, obj, form, change):
        """Override to sync booking status when payment changes"""
        if change:
            try:
                old_obj = StudioPayment.objects.get(pk=obj.pk)

                # Якщо змінився статус оплати
                if old_obj.is_paid != obj.is_paid:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Admin changed payment {obj.id} is_paid from "
                        f"'{old_obj.is_paid}' to '{obj.is_paid}'"
                    )

                    # Оновлюємо пов'язане бронювання
                    if hasattr(obj, 'booking') and obj.booking:
                        booking = obj.booking
                        if obj.is_paid and booking.status == 'pending_payment':
                            booking.status = 'paid'
                            booking.save(update_fields=['status'])
                            logger.info(f"Auto-updated booking {booking.id} to 'paid'")
                            self.message_user(
                                request,
                                f'Статус бронювання {str(booking.id)[:8]} оновлено на "Оплачено"',
                                level='success'
                            )
                        elif not obj.is_paid and booking.status == 'paid':
                            booking.status = 'pending_payment'
                            booking.save(update_fields=['status'])
                            logger.info(f"Auto-updated booking {booking.id} to 'pending_payment'")
                            self.message_user(
                                request,
                                f'Статус бронювання {str(booking.id)[:8]} повернуто на "Очікує оплати"',
                                level='warning'
                            )
            except StudioPayment.DoesNotExist:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error syncing booking status: {e}")

        super().save_model(request, obj, form, change)