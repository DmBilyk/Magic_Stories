from django.contrib import admin
from django.utils.html import format_html
from .models import StudioBooking, BookingSettings


# ВИДАЛЕНО: AdditionalServiceAdmin - тепер в studios app


@admin.register(StudioBooking)
class StudioBookingAdmin(admin.ModelAdmin):
    """Admin interface for managing studios bookings"""

    list_display = [
        'id',
        'location',  # NEW
        'customer_name',
        'booking_date',
        'booking_time',
        'duration_hours',
        'total_amount',
        'status',
        'created_at'
    ]
    list_filter = [
        'status',
        'booking_date',
        'location',  # NEW
        'created_at'
    ]
    search_fields = [
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'location__name'  # NEW
    ]
    list_editable = ['status']
    ordering = ['-booking_date', '-booking_time']
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Location', {  # NEW section
            'fields': ('location',)
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'email')
        }),
        ('Booking Details', {
            'fields': (
                'booking_date',
                'booking_time',
                'duration_hours',
                'end_time_display'
            )
        }),
        ('Services', {
            'fields': ('additional_services', 'display_services')
        }),
        ('Pricing', {
            'fields': (
                'base_price_per_hour',
                'services_total',
                'total_amount',
                'deposit_amount',
                'deposit_percentage'
            )
        }),
        ('Payment', {
            'fields': ('payment', 'payment_details')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'created_at',
        'updated_at',
        'end_time_display',
        'display_services',
        'payment_details'
    ]
    filter_horizontal = ['additional_services']

    def customer_name(self, obj):
        """Display customer full name"""
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'first_name'

    def end_time_display(self, obj):
        """Display calculated end time"""
        end_time = obj.get_end_time()
        if end_time:
            return end_time.strftime('%H:%M')
        return "N/A"
    end_time_display.short_description = 'End Time'

    def display_services(self, obj):
        """Display selected services"""
        services = obj.additional_services.all()
        if services:
            return ", ".join([f"{s.name} ({s.price} UAH)" for s in services])
        return "No additional services"
    display_services.short_description = 'Additional Services'

    def payment_details(self, obj):
        """Display payment information"""
        if obj.payment:
            status_color = 'green' if obj.payment.is_paid else 'orange'
            return format_html(
                '<span style="color: {};">Status: {}</span><br>'
                'Amount: {} UAH<br>'
                'LiqPay: {}<br>'
                'Checkbox: {}',
                status_color,
                'PAID' if obj.payment.is_paid else 'PENDING',
                obj.payment.amount,
                obj.payment.liqpay_status or 'N/A',
                obj.payment.checkbox_status or 'N/A'
            )
        return "No payment"
    payment_details.short_description = 'Payment Details'

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        """Bulk action to confirm bookings"""
        updated = queryset.filter(status='paid').update(status='confirmed')
        self.message_user(request, f'{updated} bookings marked as confirmed.')
    mark_confirmed.short_description = 'Mark selected as Confirmed'

    def mark_completed(self, request, queryset):
        """Bulk action to complete bookings"""
        updated = queryset.filter(status='confirmed').update(status='completed')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark selected as Completed'

    def mark_cancelled(self, request, queryset):
        """Bulk action to cancel bookings"""
        updated = queryset.exclude(
            status__in=['completed', 'cancelled']
        ).update(status='cancelled')
        self.message_user(request, f'{updated} bookings marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as Cancelled'

    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'location',
            'payment'
        ).prefetch_related('additional_services')


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    """Admin interface for booking settings"""

    fieldsets = (
        ('Pricing Defaults', {
            'fields': ('base_price_per_hour', 'deposit_percentage'),
            'description': 'These are default values. Actual prices may come from location settings.'
        }),
        ('Working Hours', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Booking Rules', {
            'fields': (
                'min_booking_hours',
                'max_booking_hours',
                'advance_booking_days'
            )
        }),
        ('Maintenance', {
            'fields': ('is_booking_enabled', 'maintenance_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        """Only allow one settings instance"""
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False