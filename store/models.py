from django.db import models
from category.models import Category
from django.urls import reverse

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.IntegerField()
    main_image = models.ImageField(upload_to='photos/products', help_text="Main product image", null=True, blank=True)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args = [self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='photos/products')
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of display (0 = first)")
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_date']

    def __str__(self):
        return f"{self.product.product_name} - Image {self.order + 1}"

    def save(self, *args, **kwargs):
        # Auto-generate alt text if not provided
        if not self.alt_text:
            self.alt_text = f"{self.product.product_name} - Image {self.order + 1}"
        super().save(*args, **kwargs)

class VariationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Internal name (e.g., 'color', 'size')")
    display_name = models.CharField(max_length=100, help_text="Display name (e.g., 'Color', 'Size')")
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Variation Category'
        verbose_name_plural = 'Variation Categories'
        ordering = ['display_name']

    def __str__(self):
        return self.display_name

class VariationManager(models.Manager):
    def get_variations_by_category(self, category_name):
        return self.filter(variation_category__name=category_name, is_active=True)
    
    def colors(self):
        return self.get_variations_by_category('color')
    
    def sizes(self):
        return self.get_variations_by_category('size')

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.ForeignKey(VariationCategory, on_delete=models.CASCADE)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    class Meta:
        unique_together = ('product', 'variation_category', 'variation_value')
        ordering = ['variation_category__display_name', 'variation_value']

    def __str__(self):
        return f"{self.product.product_name} - {self.variation_category.display_name}: {self.variation_value}"
