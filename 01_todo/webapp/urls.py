from django.urls import path
from . import views

urlpatterns = [
    path("", views.active, name="active"), path("completed/", views.completed, name="completed"),
    path("trash/", views.trash, name="trash"), path("tasks/new/", views.create, name="create"),
    path("tasks/<str:task_id>/edit/", views.edit, name="edit"),
    path("tasks/<str:task_id>/delete/", views.delete, name="delete"),
    path("tasks/<str:task_id>/restore/", views.restore, name="restore"),
    path("tasks/<str:task_id>/complete/", views.complete, name="complete"),
    path("tasks/<str:task_id>/move/<str:direction>/", views.move, name="move"),
    path("trash/empty/", views.empty_trash, name="empty_trash"),
]
