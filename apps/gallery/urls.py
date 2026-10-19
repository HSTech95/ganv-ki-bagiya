from django.urls import path
from . import views

app_name = "gallery"

urlpatterns = [
    # Public
    path("gallery/", views.gallery_list, name="public_list"),

    # Dashboard
    path("dashboard/gallery/", views.dashboard_gallery_list, name="dashboard_list"),
    path("dashboard/gallery/album/create/", views.dashboard_album_create, name="dashboard_album_create"),
    path("dashboard/gallery/item/upload/", views.dashboard_item_upload, name="dashboard_item_upload"),
]
