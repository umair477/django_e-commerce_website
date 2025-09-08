# Multiple Product Images Guide

## Overview

The product system has been updated to support multiple images per product, similar to modern e-commerce websites like Amazon, eBay, etc. Each product now has a main image and can have multiple additional images displayed in a gallery format.

## What Changed

### Before (Single Image)
```python
class Product(models.Model):
    images = models.ImageField(upload_to='photos/products')  # Single image only
```

### After (Multiple Images)
```python
class Product(models.Model):
    main_image = models.ImageField(upload_to='photos/products')  # Main product image

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images')
    image = models.ImageField(upload_to='photos/products')
    alt_text = models.CharField(max_length=200)  # For accessibility
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)  # Display order
```

## Features

### 1. **Main Image**
- Every product has a main image that appears in product listings
- Used in cart, checkout, and search results
- Automatically set when adding product images

### 2. **Image Gallery**
- Multiple additional images per product
- Thumbnail navigation with click-to-zoom
- Responsive design with hover effects
- Accessibility support with alt text

### 3. **Admin Interface**
- Inline image management in product admin
- Drag-and-drop ordering
- Bulk operations for multiple images
- Active/inactive image toggle

## How to Use

### 1. **Adding Images Through Admin**

#### Option A: Product Admin
1. Go to `/admin/` → Store → Products
2. Edit a product
3. Scroll down to "Product images" section
4. Add images with:
   - **Image**: Upload the image file
   - **Alt text**: Description for accessibility (auto-generated if empty)
   - **Is active**: Enable/disable the image
   - **Order**: Display order (0 = first)

#### Option B: ProductImage Admin
1. Go to `/admin/` → Store → Product Images
2. Click "Add Product Image"
3. Select the product and upload image
4. Set order and other options

### 2. **Frontend Display**

The product detail page now shows:
- **Main large image** at the top
- **Thumbnail gallery** below with clickable images
- **Smooth transitions** when switching images
- **Responsive design** for mobile devices

### 3. **Image Management Commands**

```bash
# Set main images for products that don't have one
python manage.py set_main_images
```

## Technical Implementation

### 1. **Models**
```python
class Product(models.Model):
    main_image = models.ImageField(upload_to='photos/products')
    # ... other fields

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images')
    image = models.ImageField(upload_to='photos/products')
    alt_text = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_date']
```

### 2. **Views**
```python
def product_detail(request, category_slug, product_slug):
    # ... existing code ...
    
    # Get all product images
    product_images = single_product.images.filter(is_active=True).order_by('order', 'created_date')
    
    context = {
        'single_product': single_product,
        'product_images': product_images,
        # ... other context
    }
```

### 3. **Template**
```html
<!-- Main image -->
<div class="img-big-wrap">
    <img src="{{single_product.main_image.url}}" id="main-image">
</div>

<!-- Thumbnail gallery -->
{% if product_images %}
<div class="img-small-wrap">
    <div class="item-gallery">
        <img src="{{single_product.main_image.url}}" class="img-sm" onclick="changeImage(this.src)">
        {% for image in product_images %}
            <img src="{{image.image.url}}" class="img-sm" onclick="changeImage(this.src)">
        {% endfor %}
    </div>
</div>
{% endif %}
```

### 4. **JavaScript**
```javascript
function changeImage(src) {
    document.getElementById('main-image').src = src;
    // Update active thumbnail state
}
```

## CSS Styling

The gallery includes:
- **Thumbnail grid** with flexbox layout
- **Hover effects** with smooth transitions
- **Active state** highlighting
- **Responsive design** for mobile
- **Border radius** and shadows for modern look

## Migration Notes

### Database Changes
- `Product.images` field renamed to `Product.main_image`
- New `ProductImage` model for additional images
- Existing images preserved during migration

### Template Updates
- All templates updated to use `main_image` instead of `images`
- Product listings, cart, checkout all updated
- No breaking changes to existing functionality

## Best Practices

### 1. **Image Optimization**
- Use appropriate image sizes (recommend 800x800px for main, 400x400px for thumbnails)
- Compress images for faster loading
- Use WebP format when possible

### 2. **Alt Text**
- Provide descriptive alt text for accessibility
- Auto-generated if not provided
- Include product name and image description

### 3. **Ordering**
- Set main product image as order 0
- Use logical order for additional images
- Consider product angles, details, lifestyle shots

### 4. **Performance**
- Images are lazy-loaded
- Thumbnails are optimized for gallery
- CDN recommended for production

## Example Usage

### Product Setup
1. **Main Image**: Front view of product
2. **Additional Images**:
   - Order 1: Back view
   - Order 2: Side view
   - Order 3: Detail shot
   - Order 4: Lifestyle image
   - Order 5: Size comparison

### Admin Workflow
1. Create product with main image
2. Add additional images through inline admin
3. Set order and alt text
4. Preview on frontend

## Troubleshooting

### Common Issues

1. **Images not showing**:
   - Check if images are marked as active
   - Verify file paths and permissions
   - Check media settings in Django

2. **Gallery not working**:
   - Ensure JavaScript is enabled
   - Check browser console for errors
   - Verify image URLs are correct

3. **Performance issues**:
   - Optimize image sizes
   - Use CDN for media files
   - Enable image compression

### Debug Commands
```bash
# Check products without main images
python manage.py shell -c "from store.models import Product; print(Product.objects.filter(main_image__isnull=True).count())"

# Check products with multiple images
python manage.py shell -c "from store.models import Product; [print(f'{p.product_name}: {p.images.count()} images') for p in Product.objects.all()]"
```

## Future Enhancements

1. **Image Zoom**: Magnify images on hover/click
2. **Video Support**: Add product videos
3. **360° Views**: Interactive product rotation
4. **Color Variations**: Different images per color
5. **Bulk Upload**: Drag-and-drop multiple images
6. **Image Cropping**: Built-in image editor

## Files Modified

- `store/models.py` - Added ProductImage model
- `store/admin.py` - Added admin interfaces
- `store/views.py` - Updated to provide images to template
- `templates/store/product_detail.html` - Added gallery functionality
- `templates/*.html` - Updated to use main_image field
- `store/management/commands/set_main_images.py` - Migration helper

The system now provides a professional, modern product image experience similar to major e-commerce platforms! 