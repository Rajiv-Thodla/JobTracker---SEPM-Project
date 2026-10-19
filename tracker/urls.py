
from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("activity/", views.activity, name="activity"),

    path("add/", views.add_application, name="add_application"),
    path("edit/<int:pk>/", views.edit_application, name="edit_application"),
    path("delete/<int:pk>/", views.delete_application, name="delete_application"),
    path("status/<int:pk>/", views.update_status, name="update_status"),
    path("date/<int:pk>/", views.update_event_date, name="update_event_date"),
]
