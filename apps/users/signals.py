from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import User


@receiver(post_save, sender=User)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    """
    Ensures every new user gets a corresponding UserProfile row.
    Imported lazily to avoid circular imports between apps.
    """
    if not created:
        return

    from apps.profiles.models import UserProfile

    UserProfile.objects.get_or_create(user=instance, defaults={"created_by": instance})


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    """
    Assigns the role matching account_type at creation time
    (e.g. CUSTOMER gets the CUSTOMER role automatically).
    """
    if not created:
        return

    from apps.roles.models import Role, UserRole

    role, _ = Role.objects.get_or_create(
        name=instance.account_type, defaults={"description": f"{instance.account_type} role"}
    )
    UserRole.objects.get_or_create(user=instance, role=role, defaults={"created_by": instance})
