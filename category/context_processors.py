from .models import Category


def menu_links(request):
    links = Category.objects.filter(is_active=True, parent__isnull=True)
    return {"links": links}
