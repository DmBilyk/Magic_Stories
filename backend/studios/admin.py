from django.contrib import admin
from django.utils.html import format_html
from .models import Location, AdditionalService, StudioImage


class StudioImageInline(admin.TabularInline):
    model = StudioImage
    extra = 1

    fields = ['image', 'caption', 'order', 'preview_image']
    readonly_fields = ['preview_image']

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return "No image"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin interface for managing photo studios locations"""

    list_display = [
        'name',
        'hourly_rate',
        'capacity',
        'is_active',
        'preview_image',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'address']
    list_editable = ['is_active']
    ordering = ['name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'address')
        }),
        ('Capacity & Pricing', {
            'fields': ('capacity', 'hourly_rate')
        }),
        ('Amenities', {
            'fields': ('amenities',),
            'description': 'Enter amenities as comma-separated values (e.g., "Natural Light, Backdrop System, Props")'
        }),
        ('Main Image', {
            'fields': ('image', 'preview_image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['preview_image', 'created_at', 'updated_at']
    inlines = [StudioImageInline]

    def preview_image(self, obj):
        """Display main image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: cover;" />',
                obj.image
            )
        return "No image"

    preview_image.short_description = 'Main Image'

    def get_queryset(self, request):
        """Optimize queries with prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('gallery_images')


@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    """Admin interface for managing additional services"""

    list_display = [
        'name',
        'service_id',
        'price',
        'duration_minutes',
        'is_active',
        'created_at'
    ]
    list_filter = ['service_id', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['service_id', 'name']

    fieldsets = (
        ('Service Information', {
            'fields': ('service_id', 'name', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_minutes')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    actions = ['activate_services', 'deactivate_services']

    def activate_services(self, request, queryset):
        """Bulk action to activate services"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} services activated.')

    activate_services.short_description = 'Activate selected services'

    def deactivate_services(self, request, queryset):
        """Bulk action to deactivate services"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} services deactivated.')

    deactivate_services.short_description = 'Deactivate selected services'


@admin.register(StudioImage)
class StudioImageAdmin(admin.ModelAdmin):
    """Admin interface for managing studios gallery images"""

    list_display = [
        'location',
        'caption',
        'order',
        'preview_image',
        'created_at'
    ]
    list_filter = ['location', 'created_at']
    search_fields = ['location__name', 'caption']
    list_editable = ['order']
    ordering = ['location', 'order', 'created_at']

    fieldsets = (
        ('Location', {
            'fields': ('location',)
        }),
        ('Image', {
            'fields': ('image', 'preview_image', 'caption', 'order')
        }),
    )

    readonly_fields = ['preview_image', 'created_at']

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"