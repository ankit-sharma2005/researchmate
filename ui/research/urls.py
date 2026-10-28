from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.index, name="index"),
    path("start/", views.start, name="start"),
    path("status/<str:job_id>/", views.status, name="status"),
    path("result/<str:job_id>/", views.result, name="result"),
    path("download/", views.download_report, name="download_report"),
]
