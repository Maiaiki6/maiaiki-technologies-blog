from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Post


def home(request):
    posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).select_related("category")[:6]
    categories = Category.objects.order_by("name")
    return render(request, "home.html", {"posts": posts, "categories": categories})


def blog_list(request):
    category_slug = request.GET.get("category")
    posts = Post.objects.filter(status=Post.STATUS_PUBLISHED).select_related("category")

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=selected_category)

    paginator = Paginator(posts, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.order_by("name")

    return render(
        request,
        "blog/post_list.html",
        {
            "posts": page_obj,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.STATUS_PUBLISHED)
    return render(request, "blog/post_detail.html", {"post": post})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status=Post.STATUS_PUBLISHED)
    return render(request, "blog/category_detail.html", {"category": category, "posts": posts})
