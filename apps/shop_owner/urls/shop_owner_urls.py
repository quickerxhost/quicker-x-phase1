from django.urls import path

from apps.shop_owner.views import ShopOwnerLoginView, ShopOwnerRegisterRequestView

urlpatterns = [
    path("register-request/", ShopOwnerRegisterRequestView.as_view(), name="shop-owner-register-request"),
    path("login/", ShopOwnerLoginView.as_view(), name="shop-owner-login"),
]
