from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """
    Base class for role-gated permissions. Subclass and set `required_role`.
    Expects request.user.roles (m2m through UserRole) to be queryable.
    """

    required_role = None

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return user.user_roles.filter(
            role__name=self.required_role, is_active=True, is_deleted=False
        ).exists()


class IsCustomer(HasRole):
    required_role = "CUSTOMER"


class IsShopOwner(HasRole):
    required_role = "SHOP_OWNER"


class IsAdminRole(HasRole):
    required_role = "ADMIN"


class IsSuperAdmin(HasRole):
    required_role = "SUPER_ADMIN"


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user.user_roles.filter(
            role__name__in=["ADMIN", "SUPER_ADMIN"], is_active=True, is_deleted=False
        ).exists()


class IsApprovedShopOwner(BasePermission):
    """
    Grants access only to shop owners whose registration request
    has been approved by an admin.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        request_obj = getattr(user, "shop_owner_request", None)
        return bool(request_obj and request_obj.status == "APPROVED")
