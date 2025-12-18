"""
Driver eligibility helpers for orders.

These functions are used by dispatch / driver flows to determine whether a
given driver profile is eligible to handle a specific order.

NOTE: This is v1, kept intentionally simple; more rules can be added later.
"""
from typing import Any

from drivers.models import DriverProfile
from orders.models import Order, OrderType


def is_driver_eligible_for_order(driver_profile: DriverProfile, order: Order) -> bool:
    """
    Return True if the driver is eligible to handle the given order.

    Current rules (v1):
    - FOOD     → driver_profile.accepts_food must be True
    - SHIPPING → driver_profile.accepts_shipping must be True
    - TAXI     → driver_profile.accepts_taxi must be True

    Additionally:
    - If order_type is TAXI and requested_vehicle_type is set,
      then driver_profile.vehicle_type must match requested_vehicle_type.
    - If order_type is SHIPPING and requested_delivery_type is set,
      then driver_profile.vehicle_type must match requested_delivery_type.
    """
    if order.order_type == OrderType.FOOD:
        if not driver_profile.accepts_food:
            return False

    elif order.order_type == OrderType.SHIPPING:
        if not driver_profile.accepts_shipping:
            return False

        # If a specific delivery vehicle type is requested, enforce match (v1)
        if order.requested_delivery_type and (
            driver_profile.vehicle_type != order.requested_delivery_type
        ):
            return False

    elif order.order_type == OrderType.TAXI:
        if not driver_profile.accepts_taxi:
            return False

        # If a specific vehicle type is requested for taxi, enforce match (v1)
        if order.requested_vehicle_type and (
            driver_profile.vehicle_type != order.requested_vehicle_type
        ):
            return False

    # For any other (future) order types, default to not eligible
    else:
        return False

    return True


