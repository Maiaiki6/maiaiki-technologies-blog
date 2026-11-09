from django.test import TestCase
from django.urls import reverse

from .models import Category, Post


class BlogTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("blog:home"))
        self.assertEqual(response.status_code, 200)

    def test_blog_list_is_paginated(self):
        category = Category.objects.create(name="Battery Tips")
        for i in range(10):
            Post.objects.create(
                title=f"Battery post {i}",
                category=category,
                body="A healthy battery should not drain quickly.",
                status=Post.STATUS_PUBLISHED,
            )

        response = self.client.get(reverse("blog:blog_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(response.context["posts"], "paginator"))
        self.assertGreater(response.context["posts"].paginator.num_pages, 1)

    def test_post_detail_page_loads(self):
        category = Category.objects.create(name="Battery Tips")
        post = Post.objects.create(
            title="5 signs your battery needs replacing",
            category=category,
            body="A healthy battery should not drain quickly.",
            status=Post.STATUS_PUBLISHED,
        )

        response = self.client.get(reverse("blog:post_detail", args=[post.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post.title)

    def test_post_slug_is_generated(self):
        category = Category.objects.create(name="Battery Tips")
        post = Post.objects.create(
            title="5 signs your battery needs replacing",
            category=category,
            body="A healthy battery should not drain quickly.",
            status=Post.STATUS_PUBLISHED,
        )
        self.assertEqual(post.slug, "5-signs-your-battery-needs-replacing")
