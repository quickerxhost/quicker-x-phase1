import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def delete(self):
        """Bulk soft-delete instead of hard delete."""
        return super().update(is_deleted=True, deleted_at=timezone.now(), is_active=False)

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    """Default manager: only returns non-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager that returns every row, including soft-deleted ones."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """
    Abstract base model applied to every table in the system.

    Provides:
      - UUID primary key
      - created_at / updated_at timestamps
      - created_by / updated_by actor tracking
      - is_active flag
      - is_deleted / deleted_at soft-delete support
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
    )

    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self, actor=None):
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        if actor is not None:
            self.updated_by = actor
        self.save(update_fields=["is_deleted", "is_active", "deleted_at", "updated_by", "updated_at"])

    def restore(self, actor=None):
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        if actor is not None:
            self.updated_by = actor
        self.save(update_fields=["is_deleted", "is_active", "deleted_at", "updated_by", "updated_at"])
