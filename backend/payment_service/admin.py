from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import StudioPayment


@admin.register(StudioPayment)
class StudioPaymentAdmin(admin.ModelAdmin):
    """
    Адмін-інтерфейс для моніторингу платежів
    """
    list_display = [
        'id',
        'amount',
        'payment_status',
        'liqpay_status_badge',
        'checkbox_status_badge',
        'created_at',
        'action_buttons'
    ]
    list_filter = [
        'is_paid',
        'liqpay_status',
        'checkbox_status',
        'created_at',
    ]
    search_fields = [
        'id',
        'description',
        'checkbox_receipt_id',
        'checkbox_fiscal_code',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'liqpay_status',
        'checkbox_receipt_id',
        'checkbox_fiscal_code',
        'checkbox_status',
    ]

    fieldsets = (
        ('Основна інформація', {
            'fields': ('id', 'amount', 'description', 'is_paid', 'created_at')
        }),
        ('LiqPay', {
            'fields': ('liqpay_status',),
            'classes': ('collapse',)
        }),
        ('Checkbox (РРО)', {
            'fields': ('checkbox_receipt_id', 'checkbox_fiscal_code', 'checkbox_status'),
            'classes': ('collapse',)
        }),
    )

    def payment_status(self, obj):
        """Статус оплати з кольоровою міткою"""
        if obj.is_paid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Оплачено</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⏳ Очікується</span>'
        )

    payment_status.short_description = 'Статус'

    def liqpay_status_badge(self, obj):
        """Статус від LiqPay з кольоровою міткою"""
        if not obj.liqpay_status:
            return format_html('<span style="color: gray;">—</span>')

        color_map = {
            'success': 'green',
            'sandbox': 'blue',
            'failure': 'red',
            'reversed': 'orange',
        }
        color = color_map.get(obj.liqpay_status, 'gray')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.liqpay_status
        )

    liqpay_status_badge.short_description = 'LiqPay'

    def checkbox_status_badge(self, obj):
        """Статус чека в Checkbox з кольоровою міткою"""
        if not obj.checkbox_status:
            if obj.is_paid:
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠ Відсутній чек!</span>'
                )
            return format_html('<span style="color: gray;">—</span>')

        color_map = {
            'DONE': 'green',
            'CREATED': 'blue',
            'ERROR': 'red',
        }
        color = color_map.get(obj.checkbox_status, 'gray')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.checkbox_status
        )

    checkbox_status_badge.short_description = 'Checkbox'

    def action_buttons(self, obj):
        """Кнопки дій для платежу"""
        buttons = []

        # Якщо оплачено, але немає чека - показуємо кнопку повтору
        if obj.is_paid and not obj.checkbox_receipt_id:
            retry_url = reverse('admin:retry_checkbox_receipt', args=[obj.id])
            buttons.append(
                f'<a class="button" href="{retry_url}" '
                f'style="background-color: #417690; color: white; padding: 5px 10px; '
                f'text-decoration: none; border-radius: 4px;">🔄 Створити чек</a>'
            )

        # Посилання на чек в Checkbox
        if obj.checkbox_fiscal_code:
            buttons.append(
                f'<a class="button" href="#" '
                f'style="background-color: #28a745; color: white; padding: 5px 10px; '
                f'text-decoration: none; border-radius: 4px;" target="_blank">📄 Чек</a>'
            )

        return mark_safe(' '.join(buttons)) if buttons else '—'

    action_buttons.short_description = 'Дії'

    def has_delete_permission(self, request, obj=None):
        """Забороняємо видаляти оплачені платежі"""
        if obj and obj.is_paid:
            return False
        return super().has_delete_permission(request, obj)

    class Media:
        css = {
            'all': ('admin/css/custom_payment_admin.css',)
        }