from django.db import models
from django.urls import reverse


class Category(models.Model):
    catergory_name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to="photos/category/", blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ("catergory_name",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["catergory_name"]),
            models.Index(fields=["parent", "is_active"]),
        ]

    @property
    def name(self):
        return self.catergory_name

    def get_url(self):
        return reverse("product_by_category", args=[self.slug])

    def __str__(self):
        return self.catergory_name
