from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import GalleryAlbum, GalleryItem, AlbumCategory
from .forms import GalleryAlbumForm, GalleryItemForm


def gallery_list(request):
    """
    Public gallery with category filters and lightbox view.
    """
    category_filter = request.GET.get("category", "")
    tab = request.GET.get("tab", "all")

    albums = GalleryAlbum.objects.filter(is_published=True)
    if category_filter:
        albums = albums.filter(category=category_filter)

    items = GalleryItem.objects.filter(album__is_published=True)
    if category_filter:
        items = items.filter(album__category=category_filter)

    if tab == "before_after":
        items = items.filter(is_before_after=True)

    before_after_items = GalleryItem.objects.filter(album__is_published=True, is_before_after=True)

    return render(request, "public/gallery.html", {
        "albums": albums,
        "items": items,
        "before_after_items": before_after_items,
        "category_filter": category_filter,
        "tab": tab,
        "categories": AlbumCategory.choices,
    })


# Staff Dashboard Views for Gallery
@login_required
def dashboard_gallery_list(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    albums = GalleryAlbum.objects.prefetch_related("items").all()
    album_form = GalleryAlbumForm()
    item_form = GalleryItemForm()

    return render(request, "dashboard/gallery/list.html", {
        "albums": albums,
        "album_form": album_form,
        "item_form": item_form,
    })


@login_required
def dashboard_album_create(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("gallery:dashboard_list")

    if request.method == "POST":
        form = GalleryAlbumForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save()
            messages.success(request, f"एल्बम '{album.title}' सफलतापूर्वक बनाया गया।")
    return redirect("gallery:dashboard_list")


@login_required
def dashboard_item_upload(request):
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "PRESIDENT", "PROJECT_MANAGER"]):
        messages.error(request, "Access restricted.")
        return redirect("gallery:dashboard_list")

    if request.method == "POST":
        form = GalleryItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "गैलरी फोटो/मीडिया सफलतापूर्वक अपलोड कर दी गई।")
        else:
            messages.error(request, "अपलोड करने में त्रुटि आई। कृपया फ़ाइल का प्रारूप जाँचें।")
    return redirect("gallery:dashboard_list")
