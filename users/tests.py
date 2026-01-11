from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
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


class RoleMigrationBackfillTests(TransactionTestCase):
    migrate_from = ("users", "0003_user_otp_fields")
    migrate_to = ("users", "0006_remove_user_role_field")

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        apps = self.executor.loader.project_state([self.migrate_from]).apps
        User = apps.get_model("users", "User")

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

        self.executor.migrate([self.migrate_to])
        self.apps = self.executor.loader.project_state([self.migrate_to]).apps

    def test_roles_and_profiles_backfilled(self):
        Role = self.apps.get_model("users", "Role")
        User = self.apps.get_model("users", "User")
        UserRole = self.apps.get_model("users", "UserRole")
        CustomerProfile = self.apps.get_model("users", "CustomerProfile")
        SellerProfile = self.apps.get_model("users", "SellerProfile")
        AdminProfile = self.apps.get_model("users", "AdminProfile")
        DriverProfile = self.apps.get_model("drivers", "DriverProfile")

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
        self.assertFalse(DriverProfile.objects.filter(user=driver).exists())
