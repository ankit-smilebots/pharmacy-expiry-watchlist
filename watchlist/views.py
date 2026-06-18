from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import gate
from .forms import BatchForm, UnlockForm
from .models import EXPIRY_WARNING_DAYS, Batch


def _safe_next(request, fallback="list"):
    """Only follow a ?next= that points back into this site."""
    nxt = request.GET.get("next") or request.POST.get("next")
    if nxt and url_has_allowed_host_and_scheme(
        nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return nxt
    return reverse(fallback)


def unlock(request):
    """The simple password screen."""
    if gate.is_unlocked(request):
        return redirect("list")

    if request.method == "POST":
        form = UnlockForm(request.POST)
        if form.is_valid() and gate.password_matches(form.cleaned_data["password"]):
            gate.unlock(request)
            return redirect(_safe_next(request))
        # Don't reveal whether the field was empty vs wrong — just "wrong".
        messages.error(request, "Wrong password. Please try again.")
        form = UnlockForm()
    else:
        form = UnlockForm()

    return render(request, "watchlist/unlock.html", {"form": form})


def lock(request):
    gate.lock(request)
    messages.success(request, "Locked. Your stock list is hidden.")
    return redirect("unlock")


@gate.unlock_required
def batch_list(request):
    query = (request.GET.get("q") or "").strip()

    batches = Batch.objects.all()
    if query:
        batches = batches.filter(
            Q(medicine_name__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(supplier__icontains=query)
        )

    # Model Meta already orders soonest-expiry first.
    expired = [b for b in batches if b.is_expired]
    current = [b for b in batches if not b.is_expired]
    expiring_soon_count = sum(1 for b in current if b.is_expiring_soon)

    context = {
        "expired": expired,
        "current": current,
        "expired_count": len(expired),
        "expiring_soon_count": expiring_soon_count,
        "total_count": len(expired) + len(current),
        "warning_days": EXPIRY_WARNING_DAYS,
        "query": query,
    }
    return render(request, "watchlist/list.html", context)


@gate.unlock_required
def batch_add(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Added {batch.medicine_name} (batch {batch.batch_number}).")
            return redirect("list")
    else:
        form = BatchForm()

    return render(request, "watchlist/add.html", {"form": form})


@gate.unlock_required
@require_POST
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    name, number = batch.medicine_name, batch.batch_number
    batch.delete()
    messages.success(request, f"Removed {name} (batch {number}).")
    return redirect("list")
