# backend/studios/management/commands/optimize_existing_images.py
from django.core.management.base import BaseCommand
from studios.models import Location, StudioImage


class Command(BaseCommand):
    def handle(self, *args, **options):
        for loc in Location.objects.all():
            if loc.image:
                loc.save()  # Викличе optimize_image

        for img in StudioImage.objects.all():
            if img.image:
                img.save()

        self.stdout.write('✅ Всі зображення оптимізовано!')