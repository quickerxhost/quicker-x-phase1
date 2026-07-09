from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ApplicationError
from apps.roles.models import Role, UserRole
from apps.shop_owner.models import ShopOwnerRegistrationRequest
from apps.users.models import User


@transaction.atomic
def create_shop_owner_registration(*, validated_data: dict, documents: list, images: list) -> ShopOwnerRegistrationRequest:
    """
    Creates the (inactive-for-login) User account plus the full
    registration request in a single transaction. The account cannot
    authenticate until an admin approves the request (see IsApprovedShopOwner).
    """
    email = validated_data.pop("owner_email")
    phone = validated_data.pop("owner_phone_number")
    full_name = validated_data.pop("owner_full_name")
    password = validated_data.pop("password")

    if User.objects.filter(email=email).exists():
        raise ApplicationError("An account with this email already exists.", status_code=409)

    if User.objects.filter(phone_number=phone).exists():
        raise ApplicationError("An account with this mobile number already exists.", status_code=409)

    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone_number=phone,
        account_type=User.AccountType.SHOP_OWNER,
        is_active=True,  # account exists, but login is gated by IsApprovedShopOwner
    )

    role, _ = Role.objects.get_or_create(name=Role.RoleName.SHOP_OWNER)
    UserRole.objects.get_or_create(user=user, role=role, defaults={"created_by": user})

    registration = ShopOwnerRegistrationRequest.objects.create(
        user=user,
        owner_full_name=full_name,
        owner_email=email,
        owner_phone_number=phone,
        created_by=user,
        **validated_data,
    )

    for doc in documents:
        doc.registration_request = registration
        doc.created_by = user
        doc.save()

    for img in images:
        img.registration_request = registration
        img.created_by = user
        img.save()

    return registration


def approve_registration(registration: ShopOwnerRegistrationRequest, admin_user) -> ShopOwnerRegistrationRequest:
    if registration.status == ShopOwnerRegistrationRequest.Status.APPROVED:
        raise ApplicationError("Registration is already approved.", status_code=400)

    registration.status = ShopOwnerRegistrationRequest.Status.APPROVED
    registration.reviewed_by = admin_user
    registration.reviewed_at = timezone.now()
    registration.updated_by = admin_user
    registration.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_by", "updated_at"])
    return registration


def reject_registration(registration: ShopOwnerRegistrationRequest, admin_user, reason: str) -> ShopOwnerRegistrationRequest:
    if registration.status == ShopOwnerRegistrationRequest.Status.REJECTED:
        raise ApplicationError("Registration is already rejected.", status_code=400)

    registration.status = ShopOwnerRegistrationRequest.Status.REJECTED
    registration.rejection_reason = reason
    registration.reviewed_by = admin_user
    registration.reviewed_at = timezone.now()
    registration.updated_by = admin_user
    registration.save(
        update_fields=[
            "status", "rejection_reason", "reviewed_by", "reviewed_at", "updated_by", "updated_at",
        ]
    )
    return registration
