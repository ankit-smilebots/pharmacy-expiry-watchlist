from django.urls import path

from . import views

urlpatterns = [
    path("", views.batch_list, name="list"),
    path("add/", views.batch_add, name="add"),
    path("delete/<int:pk>/", views.batch_delete, name="delete"),
    path("unlock/", views.unlock, name="unlock"),
    path("lock/", views.lock, name="lock"),
]
