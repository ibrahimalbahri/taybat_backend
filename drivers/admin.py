from django.contrib import admin

from drivers.models import DriverLocation
@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ("driver", "lat", "lng", "heading", "speed")
    search_fields = ("driver__id",)