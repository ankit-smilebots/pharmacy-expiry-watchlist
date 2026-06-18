from django.contrib import admin

from .models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("medicine_name", "batch_number", "expiry_date", "quantity", "supplier")
    list_filter = ("supplier",)
    search_fields = ("medicine_name", "batch_number", "supplier")
    ordering = ("expiry_date",)
    date_hierarchy = "expiry_date"
