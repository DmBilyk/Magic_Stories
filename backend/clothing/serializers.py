# backend/clothing/management/commands/optimize_clothing_images.py

from django.core.management.base import BaseCommand
from clothing.models import ClothingImage


class Command(BaseCommand):
    help = 'Generate thumbnails for existing clothing images'

    def handle(self, *args, **options):
        images = ClothingImage.objects.all()
        count = images.count()

        self.stdout.write(f'Found {count} images to process...')

        processed = 0
        for img in images:
            if img.image and not img.image_thumbnail:
                try:
                    self.stdout.write(f'Processing {img.id}...')
                    img.save()  # save() викличе make_thumbnail
                    processed += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing {img.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {processed} images'))