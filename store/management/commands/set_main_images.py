from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from store.models import Product, ProductImage
import os

class Command(BaseCommand):
    help = 'Set main images for products that don\'t have one'

    def handle(self, *args, **options):
        products_without_main = Product.objects.filter(main_image__isnull=True)
        
        if not products_without_main.exists():
            self.stdout.write(
                self.style.SUCCESS('All products already have main images set.')
            )
            return
        
        self.stdout.write(f'Found {products_without_main.count()} products without main images.')
        
        for product in products_without_main:
            # Try to get the first product image
            first_image = product.images.filter(is_active=True).first()
            
            if first_image:
                product.main_image = first_image.image
                product.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Set main image for {product.product_name}')
                )
            else:
                # Create a placeholder image
                self.stdout.write(
                    self.style.WARNING(f'Creating placeholder for {product.product_name}')
                )
                
                # Create a simple placeholder image using PIL
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create a 400x400 placeholder image
                    img = Image.new('RGB', (400, 400), color='#f0f0f0')
                    draw = ImageDraw.Draw(img)
                    
                    # Add text
                    text = f"No Image\n{product.product_name[:20]}"
                    try:
                        # Try to use a default font
                        font = ImageFont.load_default()
                    except:
                        font = None
                    
                    # Calculate text position (center)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (400 - text_width) // 2
                    y = (400 - text_height) // 2
                    
                    # Draw text
                    draw.text((x, y), text, fill='#666666', font=font)
                    
                    # Save to bytes
                    from io import BytesIO
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    # Create the image file
                    filename = f"placeholder_{product.id}.png"
                    product.main_image.save(filename, ContentFile(buffer.getvalue()), save=True)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Created placeholder image for {product.product_name}')
                    )
                    
                except ImportError:
                    self.stdout.write(
                        self.style.ERROR(f'PIL not available. Please install Pillow: pip install Pillow')
                    )
                    return
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating placeholder for {product.product_name}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Main image assignment completed!')
        ) 