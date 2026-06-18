from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Batch


def make_batch(name="Paracetamol", days_from_today=30, **kwargs):
    return Batch.objects.create(
        medicine_name=name,
        batch_number=kwargs.get("batch_number", "B001"),
        expiry_date=timezone.localdate() + timedelta(days=days_from_today),
        quantity=kwargs.get("quantity", 10),
        supplier=kwargs.get("supplier", "City Distributors"),
    )


class BatchModelTests(TestCase):
    def test_status_expired(self):
        b = make_batch(days_from_today=-5)
        self.assertTrue(b.is_expired)
        self.assertEqual(b.status, "expired")
        self.assertIn("Expired", b.status_label)

    def test_status_expiring_soon_within_90_days(self):
        b = make_batch(days_from_today=45)
        self.assertFalse(b.is_expired)
        self.assertTrue(b.is_expiring_soon)
        self.assertEqual(b.status, "soon")

    def test_status_ok_beyond_90_days(self):
        b = make_batch(days_from_today=200)
        self.assertFalse(b.is_expiring_soon)
        self.assertEqual(b.status, "ok")

    def test_boundary_at_90_days_is_soon(self):
        self.assertEqual(make_batch(days_from_today=90).status, "soon")
        self.assertEqual(make_batch(days_from_today=91).status, "ok")

    def test_default_ordering_soonest_first(self):
        make_batch(name="Late", days_from_today=100)
        make_batch(name="Soon", days_from_today=5)
        make_batch(name="Mid", days_from_today=40)
        names = [b.medicine_name for b in Batch.objects.all()]
        self.assertEqual(names, ["Soon", "Mid", "Late"])


@override_settings(WATCHLIST_PASSWORD="testpass")
class GateTests(TestCase):
    def test_list_requires_unlock(self):
        resp = self.client.get(reverse("list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("unlock"), resp.url)

    def test_wrong_password_does_not_unlock(self):
        resp = self.client.post(reverse("unlock"), {"password": "nope"})
        self.assertEqual(resp.status_code, 200)  # re-renders with error
        self.assertContains(resp, "Wrong password")
        # Still locked.
        self.assertEqual(self.client.get(reverse("list")).status_code, 302)

    def test_correct_password_unlocks(self):
        resp = self.client.post(reverse("unlock"), {"password": "testpass"})
        self.assertRedirects(resp, reverse("list"))
        self.assertEqual(self.client.get(reverse("list")).status_code, 200)

    def test_safe_next_redirect(self):
        resp = self.client.post(
            reverse("unlock") + "?next=" + reverse("add"), {"password": "testpass"}
        )
        self.assertRedirects(resp, reverse("add"))

    def test_open_redirect_is_blocked(self):
        resp = self.client.post(
            reverse("unlock") + "?next=https://evil.example.com", {"password": "testpass"}
        )
        self.assertRedirects(resp, reverse("list"))

    def test_lock_clears_session(self):
        self.client.post(reverse("unlock"), {"password": "testpass"})
        self.client.get(reverse("lock"))
        self.assertEqual(self.client.get(reverse("list")).status_code, 302)


@override_settings(WATCHLIST_PASSWORD="testpass")
class WorkflowTests(TestCase):
    def setUp(self):
        self.client.post(reverse("unlock"), {"password": "testpass"})

    def test_add_batch(self):
        resp = self.client.post(reverse("add"), {
            "medicine_name": "Amoxicillin",
            "batch_number": "AMX-22",
            "expiry_date": (timezone.localdate() + timedelta(days=20)).isoformat(),
            "quantity": 30,
            "supplier": "MedSupply",
        })
        self.assertRedirects(resp, reverse("list"))
        self.assertTrue(Batch.objects.filter(medicine_name="Amoxicillin").exists())

    def test_list_separates_expired_and_sorts(self):
        make_batch(name="Expired1", days_from_today=-3)
        make_batch(name="SoonOne", days_from_today=10)
        make_batch(name="LaterOne", days_from_today=300)
        resp = self.client.get(reverse("list"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["expired"]), 1)
        self.assertEqual(resp.context["expired"][0].medicine_name, "Expired1")
        current_names = [b.medicine_name for b in resp.context["current"]]
        self.assertEqual(current_names, ["SoonOne", "LaterOne"])
        self.assertEqual(resp.context["expiring_soon_count"], 1)

    def test_search_filters(self):
        make_batch(name="Crocin")
        make_batch(name="Dolo")
        resp = self.client.get(reverse("list"), {"q": "croc"})
        names = [b.medicine_name for b in resp.context["current"]]
        self.assertEqual(names, ["Crocin"])

    def test_delete_batch(self):
        b = make_batch()
        resp = self.client.post(reverse("delete", args=[b.pk]))
        self.assertRedirects(resp, reverse("list"))
        self.assertFalse(Batch.objects.filter(pk=b.pk).exists())

    def test_delete_requires_post(self):
        b = make_batch()
        resp = self.client.get(reverse("delete", args=[b.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Batch.objects.filter(pk=b.pk).exists())
