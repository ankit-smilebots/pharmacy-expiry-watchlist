"""A deliberately simple single-password gate.

Iqbal Bhai asked for just a password so customers at the counter can't see his
stock list — not full user accounts. We compare the submitted password against
WATCHLIST_PASSWORD (kept in the environment, never in the repo) and remember the
unlocked state in the session.
"""

import hmac
from functools import wraps

from django.conf import settings
from django.shortcuts import redirect

SESSION_KEY = "watchlist_unlocked"


def password_matches(raw_password):
    """Constant-time comparison against the configured password."""
    expected = settings.WATCHLIST_PASSWORD or ""
    return hmac.compare_digest(str(raw_password), str(expected))


def is_unlocked(request):
    return bool(request.session.get(SESSION_KEY))


def unlock(request):
    request.session[SESSION_KEY] = True


def lock(request):
    request.session.pop(SESSION_KEY, None)


def unlock_required(view_func):
    """Redirect to the unlock screen if the session isn't unlocked yet."""

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_unlocked(request):
            login_url = redirect("unlock").url
            return redirect(f"{login_url}?next={request.path}")
        return view_func(request, *args, **kwargs)

    return wrapped
