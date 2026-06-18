from django.db import models
from django.utils import timezone

# Anything expiring within this many days is flagged as "expiring soon".
EXPIRY_WARNING_DAYS = 90


class Batch(models.Model):
    """A single batch of a medicine sitting in the store."""

    medicine_name = models.CharField("Medicine name", max_length=200)
    batch_number = models.CharField("Batch number", max_length=100)
    expiry_date = models.DateField("Expiry date")
    quantity = models.PositiveIntegerField("Quantity")
    supplier = models.CharField("Supplier", max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Soonest-to-expire first — this is how Iqbal Bhai checks his stock.
        ordering = ["expiry_date", "medicine_name"]
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.medicine_name} ({self.batch_number})"

    # --- Expiry helpers -------------------------------------------------

    @property
    def days_left(self):
        """Days until expiry. Negative means already expired."""
        return (self.expiry_date - timezone.localdate()).days

    @property
    def is_expired(self):
        return self.days_left < 0

    @property
    def is_expiring_soon(self):
        """Not yet expired, but within the warning window."""
        return 0 <= self.days_left <= EXPIRY_WARNING_DAYS

    @property
    def status(self):
        if self.is_expired:
            return "expired"
        if self.is_expiring_soon:
            return "soon"
        return "ok"

    @property
    def status_label(self):
        days = self.days_left
        if days < -1:
            return f"Expired {abs(days)} days ago"
        if days == -1:
            return "Expired yesterday"
        if days == 0:
            return "Expires today"
        if days == 1:
            return "Expires tomorrow"
        return f"{days} days left"
