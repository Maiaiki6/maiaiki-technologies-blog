from django.db import models


class QuoteRequest(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    device = models.CharField(max_length=150)
    issue = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.device}"
