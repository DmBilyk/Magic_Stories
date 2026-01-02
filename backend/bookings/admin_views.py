from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@user_passes_test(lambda u: u.is_staff)
@ensure_csrf_cookie
def admin_booking_panel(request):
    """
    Render the React admin panel for managing bookings.
    Only accessible to staff users.
    """
    return render(request, 'bookings/admin_panel', {
        'title': 'Admin Booking Management'
    })