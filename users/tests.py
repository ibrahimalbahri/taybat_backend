from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from users.models import User
from users.permissions import IsAdmin


class RoleHelperTests(TestCase):
    def test_add_and_remove_role(self):
        user = User.objects.create_user(
            email="role@example.com",
            name="Role User",
            phone="2000",
        )

        user.add_role("customer")
        self.assertTrue(user.has_role("customer"))

        user.remove_role("customer")
        self.assertFalse(user.has_role("customer"))


class PermissionRoleTests(TestCase):
    def test_is_admin_uses_roles(self):
        factory = APIRequestFactory()
        request = factory.get("/api/admin/")

        user = User.objects.create_user(
            email="admin-check@example.com",
            name="Admin Check",
            phone="2001",
        )
        request.user = user

        permission = IsAdmin()
        self.assertFalse(permission.has_permission(request, None))

        user.add_role("admin")
        self.assertTrue(permission.has_permission(request, None))


class RoleMigrationBackfillTests(TestCase):
    def test_roles_and_profiles_backfilled(self):
        import importlib

        migration_module = importlib.import_module(
            "users.migrations.0005_backfill_roles_profiles"
        )
        backfill_roles_and_profiles = migration_module.backfill_roles_and_profiles

        executor = MigrationExecutor(connection)
        apps = executor.loader.project_state([("users", "0005_backfill_roles_profiles")]).apps
        User = apps.get_model("users", "User")
        Role = apps.get_model("users", "Role")
        UserRole = apps.get_model("users", "UserRole")
        CustomerProfile = apps.get_model("users", "CustomerProfile")
        SellerProfile = apps.get_model("users", "SellerProfile")
        AdminProfile = apps.get_model("users", "AdminProfile")
        from drivers.models import DriverProfile

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(users_user)")
            columns = {row[1] for row in cursor.fetchall()}
            if "role" not in columns:
                cursor.execute("ALTER TABLE users_user ADD COLUMN role varchar(20)")

        User.objects.create(
            name="Customer",
            email="cust@example.com",
            phone="3000",
            role="CUSTOMER",
        )
        User.objects.create(
            name="Seller",
            email="seller@example.com",
            phone="3001",
            role="SELLER",
        )
        User.objects.create(
            name="Admin",
            email="admin@example.com",
            phone="3002",
            role="ADMIN",
        )
        User.objects.create(
            name="Driver",
            email="driver@example.com",
            phone="3003",
            role="DRIVER",
        )

        backfill_roles_and_profiles(apps, None)

        self.assertTrue(Role.objects.filter(name="customer").exists())
        self.assertTrue(Role.objects.filter(name="driver").exists())
        self.assertTrue(Role.objects.filter(name="seller").exists())
        self.assertTrue(Role.objects.filter(name="admin").exists())

        customer = User.objects.get(email="cust@example.com")
        seller = User.objects.get(email="seller@example.com")
        admin = User.objects.get(email="admin@example.com")
        driver = User.objects.get(email="driver@example.com")

        self.assertTrue(UserRole.objects.filter(user=customer, role__name="customer").exists())
        self.assertTrue(UserRole.objects.filter(user=seller, role__name="seller").exists())
        self.assertTrue(UserRole.objects.filter(user=admin, role__name="admin").exists())
        self.assertTrue(UserRole.objects.filter(user=driver, role__name="driver").exists())

        self.assertTrue(CustomerProfile.objects.filter(user=customer).exists())
        self.assertTrue(SellerProfile.objects.filter(user=seller).exists())
        self.assertTrue(AdminProfile.objects.filter(user=admin).exists())
        self.assertFalse(DriverProfile.objects.filter(user_id=driver.id).exists())
