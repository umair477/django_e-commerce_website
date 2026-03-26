from django.urls import path

from . import views


urlpatterns = [
    path("", views.store, name="store"),
    path("category/<slug:category_slug>/", views.store, name="product_by_category"),
    path("category/<slug:category_slug>/<slug:product_slug>/", views.product_detail, name="product_detail"),
    path("search/", views.search, name="search"),
    path("wishlist/<int:product_id>/toggle/", views.toggle_wishlist, name="toggle_wishlist"),
    path("reviews/<int:product_id>/submit/", views.submit_review, name="submit_review"),
]
