from django.test import TestCase, Client
from django.urls import reverse
from apps.gallery.models import GalleryAlbum, GalleryItem, AlbumCategory


class GalleryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.album = GalleryAlbum.objects.create(
            title="Tree Plantation Summer 2026",
            category=AlbumCategory.TREE_PLANTATION,
            description="Villagers planting trees",
            is_published=True
        )
        self.item = GalleryItem.objects.create(
            album=self.album,
            title="Tree Plantation Summer 2026",
            media_type="PHOTO"
        )

    def test_album_slug_generation(self):
        self.assertTrue(self.album.slug.startswith("tree-plantation"))
        self.assertTrue(self.album.is_published)

    def test_public_gallery_view(self):
        response = self.client.get(reverse("gallery:public_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tree Plantation Summer 2026")
