from django.contrib import admin

from .models import QuoteRequest


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "device", "created_at"]
    search_fields = ["full_name", "phone", "device", "issue"]
    list_filter = ["created_at"]
