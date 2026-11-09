from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from blog.models import Post

from .models import QuoteRequest


def services(request):
    return render(request, "shop/services.html")


def robots_txt(request):
    content = """User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {site_url}/sitemap.xml\n""".format(site_url=settings.SITE_URL)
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    site_url = settings.SITE_URL.rstrip("/")
    urls = [
        "",
        "/blog/",
        "/shop/services/",
        "/shop/quote/",
    ]
    blog_posts = Post.objects.filter(status=Post.STATUS_PUBLISHED)
    for post in blog_posts:
        urls.append(f"/blog/{post.slug}/")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{site_url}{path}</loc>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return HttpResponse("\n".join(xml), content_type="application/xml")


def quote_request(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        device = request.POST.get("device", "").strip()
        issue = request.POST.get("issue", "").strip()
        website = request.POST.get("website", "").strip()

        if website:
            return render(request, "shop/quote.html", {"error": "Please try again. Your message was flagged as spam."})

        if full_name and phone and device and issue:
            quote = QuoteRequest.objects.create(
                full_name=full_name,
                phone=phone,
                device=device,
                issue=issue,
            )
            message = (
                f"New quote request from {quote.full_name}\n"
                f"Phone: {quote.phone}\n"
                f"Device: {quote.device}\n\n"
                f"Issue:\n{quote.issue}"
            )
            try:
                send_mail(
                    subject="New quote request from MAIAIKI TECHNOLOGIES",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
            return redirect("shop:quote_thanks")

    return render(request, "shop/quote.html")


def quote_thanks(request):
    return render(request, "shop/quote_thanks.html")
