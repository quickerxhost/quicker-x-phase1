from django.urls import path

from apps.shop_owner.views import (
    AdminPendingShopOwnerListView,
    AdminShopOwnerApproveView,
    AdminShopOwnerRejectView,
)

urlpatterns = [
    path("pending/", AdminPendingShopOwnerListView.as_view(), name="admin-shop-owner-pending"),
    path("<uuid:pk>/approve/", AdminShopOwnerApproveView.as_view(), name="admin-shop-owner-approve"),
    path("<uuid:pk>/reject/", AdminShopOwnerRejectView.as_view(), name="admin-shop-owner-reject"),
]
