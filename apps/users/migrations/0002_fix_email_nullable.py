from django.db import migrations


def drop_email_not_null(apps, schema_editor):
    """
    Only Postgres has the stale NOT NULL constraint on this column (it was
    created before migrations existed for this app). SQLite/other backends
    used in local testing don't have this drift, so skip them safely.
    """
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "users" ALTER COLUMN "email" DROP NOT NULL;')


class Migration(migrations.Migration):
    """
    The live production 'users' table was created with `email` as NOT NULL,
    even though the model (and 0001_initial's migration state) has always
    said `null=True`. Django's migration history considered 0001_initial
    already applied, so `migrate` never actually touched the real column.

    This migration forces the real database column to match the model by
    issuing an explicit ALTER TABLE, regardless of what the migration state
    already believes. Safe to run even if the column is already nullable,
    and safe to run on non-Postgres backends (it's a no-op there).
    """

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(drop_email_not_null, reverse_code=migrations.RunPython.noop),
    ]
