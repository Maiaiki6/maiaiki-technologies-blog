from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.services, name="index"),
    path("services/", views.services, name="services"),
    path("quote/", views.quote_request, name="quote"),
    path("quote/thanks/", views.quote_thanks, name="quote_thanks"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
]
