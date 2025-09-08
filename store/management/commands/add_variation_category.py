from django.core.management.base import BaseCommand
from store.models import VariationCategory

class Command(BaseCommand):
    help = 'Add a new variation category'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Internal name (e.g., "color", "size")')
        parser.add_argument('display_name', type=str, help='Display name (e.g., "Color", "Size")')

    def handle(self, *args, **options):
        name = options['name']
        display_name = options['display_name']
        
        try:
            category, created = VariationCategory.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created variation category: {display_name} ({name})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Variation category already exists: {display_name} ({name})')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating variation category: {e}')
            ) 