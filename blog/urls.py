from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.post_detail, name="post_detail"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
]
