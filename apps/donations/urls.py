from django.urls import path
from . import views

app_name = "donations"

urlpatterns = [
    # Public
    path("donations/", views.public_donations_list, name="public_list"),
    path("donate/", views.donate_view, name="donate"),
    path("donate/upi/<str:donation_id>/", views.donate_upi_view, name="donate_upi"),
    path("donate/gateway/<str:donation_id>/", views.donate_gateway_view, name="donate_gateway"),
    path("donate/thank-you/<str:donation_id>/", views.donate_thankyou_view, name="donate_thankyou"),
    path("receipt/<str:receipt_number>/", views.public_receipt_view, name="public_receipt"),

    # Dashboard
    path("dashboard/donations/", views.dashboard_donations_list, name="dashboard_list"),
    path("dashboard/donations/create/", views.dashboard_donation_create, name="dashboard_create"),
    path("dashboard/donations/<str:donation_id>/", views.dashboard_donation_detail, name="dashboard_detail"),
    path("dashboard/donations/<str:donation_id>/verify/", views.dashboard_donation_verify, name="dashboard_verify"),
]
