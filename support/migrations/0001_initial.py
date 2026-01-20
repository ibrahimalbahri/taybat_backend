from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0009_alter_order_customer"),
        ("sellers", "0006_merge_20260113_1918"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requester_role", models.CharField(choices=[("CUSTOMER", "Customer"), ("SELLER", "Seller"), ("DRIVER", "Driver")], max_length=20)),
                ("subject", models.CharField(max_length=255)),
                ("category", models.CharField(choices=[("ORDER", "Order"), ("PAYMENT", "Payment"), ("DELIVERY", "Delivery"), ("ACCOUNT", "Account"), ("OTHER", "Other")], max_length=20)),
                ("priority", models.CharField(choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("URGENT", "Urgent")], default="MEDIUM", max_length=20)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("IN_PROGRESS", "In progress"), ("WAITING_ON_CUSTOMER", "Waiting on customer"), ("RESOLVED", "Resolved"), ("CLOSED", "Closed")], default="OPEN", max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_activity_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_support_tickets", to=settings.AUTH_USER_MODEL)),
                ("driver", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="driver_support_tickets", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_tickets", to="orders.order")),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="support_tickets", to=settings.AUTH_USER_MODEL)),
                ("restaurant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_tickets", to="sellers.restaurant")),
            ],
            options={
                "verbose_name": "Support Ticket",
                "verbose_name_plural": "Support Tickets",
            },
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_role", models.CharField(choices=[("CUSTOMER", "Customer"), ("SELLER", "Seller"), ("DRIVER", "Driver"), ("STAFF", "Staff")], max_length=20)),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_messages", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="support.supportticket")),
            ],
            options={
                "verbose_name": "Support Message",
                "verbose_name_plural": "Support Messages",
            },
        ),
        migrations.CreateModel(
            name="SupportAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_url", models.URLField()),
                ("mime_type", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="support.supportmessage")),
            ],
            options={
                "verbose_name": "Support Attachment",
                "verbose_name_plural": "Support Attachments",
            },
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["status", "priority", "created_at"], name="support_sup_status_5ffb9d_idx"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["requester", "created_at"], name="support_sup_request_4d00f4_idx"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["assigned_to", "status"], name="support_sup_assigne_2f0f2a_idx"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["order"], name="support_sup_order_e0c9b4_idx"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["restaurant"], name="support_sup_restaur_f77bc8_idx"),
        ),
        migrations.AddIndex(
            model_name="supportmessage",
            index=models.Index(fields=["ticket", "created_at"], name="support_sup_ticket_6a0278_idx"),
        ),
        migrations.AddIndex(
            model_name="supportattachment",
            index=models.Index(fields=["message"], name="support_sup_message_f25b99_idx"),
        ),
    ]
