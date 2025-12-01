from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PropCategory,
    PropItem,
    PropImage,
    BookingPropItem,
    PropRentalSettings
)


class PropImageInline(admin.TabularInline):
    model = PropImage
    extra = 1
    fields = ['image', 'alt_text', 'order', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return '-'

    image_preview.short_description = 'Preview'


@admin.register(PropCategory)
class PropCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'items_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

    def items_count(self, obj):
        return obj.items.filter(is_active=True).count()

    items_count.short_description = 'Active Items'


@admin.register(PropItem)
class PropItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'quantity',
        'availability_badge', 'primary_image_preview', 'created_at'
    ]
    list_filter = ['is_active', 'is_available', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PropImageInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Details', {
            'fields': ('price', 'quantity')
        }),
        ('Availability', {
            'fields': ('is_available', 'is_active')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def availability_badge(self, obj):
        if obj.is_active and obj.is_available:
            color = 'green'
            text = 'Available'
        elif obj.is_active:
            color = 'orange'
            text = 'Not Available'
        else:
            color = 'red'
            text = 'Inactive'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, text
        )

    availability_badge.short_description = 'Status'

    def primary_image_preview(self, obj):
        image = obj.images.first()
        if image and image.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                image.image.url
            )
        return '-'

    primary_image_preview.short_description = 'Image'


@admin.register(PropImage)
class PropImageAdmin(admin.ModelAdmin):
    list_display = ['prop_item', 'image_preview', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['prop_item__name', 'alt_text']
    ordering = ['prop_item', 'order']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return '-'

    image_preview.short_description = 'Preview'


@admin.register(BookingPropItem)
class BookingPropItemAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id', 'booking_date', 'prop_item', 'quantity',
        'price_at_booking', 'total_price', 'booking_status'
    ]
    list_filter = ['booking__status', 'booking__booking_date', 'created_at']
    search_fields = [
        'booking__id', 'booking__first_name', 'booking__last_name',
        'prop_item__name'
    ]
    readonly_fields = ['price_at_booking', 'created_at', 'total_price']
    raw_id_fields = ['booking', 'prop_item']

    def booking_id(self, obj):
        return str(obj.booking.id)[:8]

    booking_id.short_description = 'Booking ID'

    def booking_date(self, obj):
        return obj.booking.booking_date

    booking_date.short_description = 'Date'
    booking_date.admin_order_field = 'booking__booking_date'

    def total_price(self, obj):
        return f"{obj.get_total_price()} UAH"

    total_price.short_description = 'Total Price'

    def booking_status(self, obj):
        status = obj.booking.status
        colors = {
            'pending_payment': 'orange',
            'paid': 'blue',
            'confirmed': 'green',
            'cancelled': 'red',
            'completed': 'gray'
        }
        color = colors.get(status, 'gray')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, status.replace('_', ' ').title()
        )

    booking_status.short_description = 'Booking Status'


@admin.register(PropRentalSettings)
class PropRentalSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'max_items_per_booking', 'is_rental_enabled', 'updated_at'
    ]
    readonly_fields = ['updated_at']

    fieldsets = (
        ('General Settings', {
            'fields': ('is_rental_enabled', 'max_items_per_booking')
        }),
        ('Terms & Conditions', {
            'fields': ('rental_terms',)
        }),
        ('System Info', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not PropRentalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False