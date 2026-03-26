from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from store.sitemaps import CategorySitemap, ProductSitemap

from . import views


sitemaps = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
}


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("store/", include("store.urls")),
    path("cart/", include("carts.urls")),
    path("accounts/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
