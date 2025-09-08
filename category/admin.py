from django.contrib import admin
from . models import Category


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('catergory_name',)}
    list_display = ('catergory_name', 'slug')
# Register your models here.
admin.site.register(Category, CategoryAdmin)