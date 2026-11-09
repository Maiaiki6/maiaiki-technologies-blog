from django.contrib import admin
from django.urls import include, path

from shop.views import robots_txt, sitemap_xml

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    path("", include(("blog.urls", "blog"), namespace="blog")),
    path("shop/", include(("shop.urls", "shop"), namespace="shop")),
]
