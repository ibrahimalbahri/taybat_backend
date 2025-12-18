"""
Pricing service for calculating order quotes.

This module computes:
- Distance via Haversine formula
- Quotes for TAXI and SHIPPING based on configurable rates
- Returns a consistent quote structure for preview and checkout
"""
import math
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass

from orders.models import OrderType, VehicleType


# Earth's radius in kilometers
EARTH_RADIUS_KM = 6371.0


@dataclass
class QuoteResult:
    """
    Consistent quote structure returned by pricing service.
    Maps to Order model fields.
    """
    calculated_distance: Decimal  # Distance in km
    calculated_time: Optional[int] = None  # Estimated time in seconds
    subtotal_amount: Decimal = Decimal("0.00")  # Base fare/fee
    discount_amount: Decimal = Decimal("0.00")  # Discounts (0 for v1)
    delivery_fee: Decimal = Decimal("0.00")  # Per-km charges (service fee for taxi/shipping)
    total_amount: Decimal = Decimal("0.00")  # Final total (subtotal + delivery_fee + tip)


# Pricing configuration (v1 - simple deterministic rates)
# These can be moved to settings or database in the future

TAXI_RATES = {
    VehicleType.BIKE: {
        "base_fare": Decimal("5.00"),  # Base fare in local currency
        "per_km": Decimal("2.00"),  # Per kilometer rate
    },
    VehicleType.MOTOR: {
        "base_fare": Decimal("8.00"),
        "per_km": Decimal("2.50"),
    },
    VehicleType.CAR: {
        "base_fare": Decimal("12.00"),
        "per_km": Decimal("3.00"),
    },
    VehicleType.VAN: {
        "base_fare": Decimal("15.00"),
        "per_km": Decimal("4.00"),
    },
}

SHIPPING_RATES = {
    VehicleType.BIKE: {
        "base_fee": Decimal("3.00"),
        "per_km": Decimal("1.50"),
        "weight_multiplier": Decimal("0.10"),  # Per kg multiplier
    },
    VehicleType.MOTOR: {
        "base_fee": Decimal("5.00"),
        "per_km": Decimal("2.00"),
        "weight_multiplier": Decimal("0.15"),
    },
    VehicleType.CAR: {
        "base_fee": Decimal("8.00"),
        "per_km": Decimal("2.50"),
        "weight_multiplier": Decimal("0.20"),
    },
    VehicleType.VAN: {
        "base_fee": Decimal("10.00"),
        "per_km": Decimal("3.00"),
        "weight_multiplier": Decimal("0.25"),
    },
}

# Average speeds for time estimation (km/h)
AVERAGE_SPEEDS = {
    VehicleType.BIKE: 20,  # km/h
    VehicleType.MOTOR: 40,
    VehicleType.CAR: 50,
    VehicleType.VAN: 45,
}


def haversine_distance(
    lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal
) -> Decimal:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in kilometers as Decimal
    """
    # Convert Decimal to float for calculations
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    
    distance_km = EARTH_RADIUS_KM * c
    
    # Round to 3 decimal places and return as Decimal
    return Decimal(str(round(distance_km, 3)))


def calculate_estimated_time(
    distance_km: Decimal, vehicle_type: Optional[str] = None
) -> Optional[int]:
    """
    Calculate estimated delivery time based on distance and vehicle type.
    
    Args:
        distance_km: Distance in kilometers
        vehicle_type: Vehicle type (BIKE, MOTOR, CAR, VAN)
    
    Returns:
        Estimated time in seconds, or None if vehicle_type not provided
    """
    if not vehicle_type or vehicle_type not in AVERAGE_SPEEDS:
        return None
    
    speed_kmh = AVERAGE_SPEEDS[vehicle_type]
    time_hours = float(distance_km) / speed_kmh
    time_seconds = int(time_hours * 3600)
    
    return time_seconds


def calculate_taxi_quote(
    distance_km: Decimal,
    vehicle_type: str,
    tip: Decimal = Decimal("0.00"),
) -> QuoteResult:
    """
    Calculate taxi quote based on distance and vehicle type.
    
    Args:
        distance_km: Distance in kilometers
        vehicle_type: Vehicle type (BIKE, MOTOR, CAR, VAN)
        tip: Optional tip amount
    
    Returns:
        QuoteResult with calculated pricing
    
    Raises:
        ValueError: If vehicle_type is not supported
    """
    if vehicle_type not in TAXI_RATES:
        raise ValueError(f"Unsupported vehicle type for taxi: {vehicle_type}")
    
    rates = TAXI_RATES[vehicle_type]
    base_fare = rates["base_fare"]
    per_km_rate = rates["per_km"]
    
    # Calculate service fee (per-km charges)
    service_fee = per_km_rate * distance_km
    
    # Delivery fee is the per-km service fee
    delivery_fee = service_fee.quantize(Decimal("0.01"))
    
    # Subtotal = base fare + delivery_fee (combined for total calculation)
    subtotal = (base_fare + delivery_fee).quantize(Decimal("0.01"))
    
    # Total = subtotal + tip (as per requirement)
    total = (subtotal + tip).quantize(Decimal("0.01"))
    
    # Calculate estimated time
    estimated_time = calculate_estimated_time(distance_km, vehicle_type)
    
    return QuoteResult(
        calculated_distance=distance_km,
        calculated_time=estimated_time,
        subtotal_amount=subtotal,
        discount_amount=Decimal("0.00"),
        delivery_fee=delivery_fee,
        total_amount=total,
    )


def calculate_shipping_quote(
    distance_km: Decimal,
    delivery_type: str,
    weight_kg: Optional[Decimal] = None,
    tip: Decimal = Decimal("0.00"),
) -> QuoteResult:
    """
    Calculate shipping quote based on distance, delivery type, and optional weight.
    
    Args:
        distance_km: Distance in kilometers
        delivery_type: Delivery vehicle type (BIKE, MOTOR, CAR, VAN)
        weight_kg: Optional package weight in kilograms
        tip: Optional tip amount
    
    Returns:
        QuoteResult with calculated pricing
    
    Raises:
        ValueError: If delivery_type is not supported
    """
    if delivery_type not in SHIPPING_RATES:
        raise ValueError(f"Unsupported delivery type for shipping: {delivery_type}")
    
    rates = SHIPPING_RATES[delivery_type]
    base_fee = rates["base_fee"]
    per_km_rate = rates["per_km"]
    weight_multiplier = rates["weight_multiplier"]
    
    # Calculate base service fee (per-km charges)
    service_fee = per_km_rate * distance_km
    
    # Add weight multiplier if weight is provided
    if weight_kg is not None:
        weight_charge = weight_multiplier * weight_kg
        service_fee += weight_charge
    
    # Delivery fee is the calculated service fee (per-km + weight)
    delivery_fee = service_fee.quantize(Decimal("0.01"))
    
    # Subtotal = base fee + delivery_fee (combined for total calculation)
    subtotal = (base_fee + delivery_fee).quantize(Decimal("0.01"))
    
    # Total = subtotal + tip (as per requirement)
    total = (subtotal + tip).quantize(Decimal("0.01"))
    
    # Calculate estimated time
    estimated_time = calculate_estimated_time(distance_km, delivery_type)
    
    return QuoteResult(
        calculated_distance=distance_km,
        calculated_time=estimated_time,
        subtotal_amount=subtotal,
        discount_amount=Decimal("0.00"),
        delivery_fee=delivery_fee,
        total_amount=total,
    )


def calculate_quote(
    order_type: str,
    pickup_lat: Decimal,
    pickup_lng: Decimal,
    dropoff_lat: Decimal,
    dropoff_lng: Decimal,
    vehicle_type: Optional[str] = None,
    delivery_type: Optional[str] = None,
    weight_kg: Optional[Decimal] = None,
    tip: Decimal = Decimal("0.00"),
) -> QuoteResult:
    """
    Main function to calculate quote for any order type.
    
    Args:
        order_type: Order type (FOOD, TAXI, SHIPPING)
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        dropoff_lat: Dropoff latitude
        dropoff_lng: Dropoff longitude
        vehicle_type: Vehicle type for TAXI (required for TAXI)
        delivery_type: Delivery type for SHIPPING (required for SHIPPING)
        weight_kg: Package weight for SHIPPING (optional)
        tip: Optional tip amount
    
    Returns:
        QuoteResult with calculated pricing
    
    Raises:
        ValueError: If order_type is not supported or required parameters are missing
    """
    # Calculate distance
    distance_km = haversine_distance(
        pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
    )
    
    if order_type == OrderType.TAXI:
        if not vehicle_type:
            raise ValueError("vehicle_type is required for TAXI orders")
        return calculate_taxi_quote(distance_km, vehicle_type, tip)
    
    elif order_type == OrderType.SHIPPING:
        if not delivery_type:
            raise ValueError("delivery_type is required for SHIPPING orders")
        return calculate_shipping_quote(distance_km, delivery_type, weight_kg, tip)
    
    elif order_type == OrderType.FOOD:
        # Food orders use different pricing logic (restaurant-based)
        # For now, return a minimal quote with just distance
        # Food pricing should be handled separately in checkout
        return QuoteResult(
            calculated_distance=distance_km,
            calculated_time=None,
            subtotal_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            delivery_fee=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )
    
    else:
        raise ValueError(f"Unsupported order type: {order_type}")

