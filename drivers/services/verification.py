"""
Service-layer functions for driver verification workflow.
"""
from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from drivers.models import (
    DriverProfile,
    DriverStatus,
    DriverVerification,
    DriverVerificationStatus,
)
from users.models import User


class DriverVerificationError(Exception):
    """Base exception for driver verification domain errors."""


class DriverAlreadyVerified(DriverVerificationError):
    """Raised when attempting to re-verify an already approved/rejected driver."""


@dataclass
class DriverVerificationResult:
    verification: DriverVerification
    profile: DriverProfile


@transaction.atomic
def verify_driver(
    *,
    admin_user: User,
    driver_user_id: int,
    status: str,
    notes: Optional[str] = None,
) -> DriverVerificationResult:
    """
    Atomically verify a driver (approve/reject).

    - Locks the DriverProfile row
    - Ensures idempotency: cannot re-verify once approved/rejected
    - Updates DriverProfile.status accordingly
    - Creates a DriverVerification record
    """
    try:
        profile = (
            DriverProfile.objects.select_for_update()
            .select_related("user")
            .get(user_id=driver_user_id)
        )
    except DriverProfile.DoesNotExist:
        raise DriverVerificationError("DriverProfile not found for this user.")

    if profile.status in (DriverStatus.APPROVED, DriverStatus.REJECTED):
        raise DriverAlreadyVerified(
            f"Driver already verified with status={profile.status}."
        )

    if status not in (
        DriverVerificationStatus.APPROVED,
        DriverVerificationStatus.REJECTED,
    ):
        raise DriverVerificationError("Invalid verification status.")

    # Update profile status to match verification
    profile.status = (
        DriverStatus.APPROVED
        if status == DriverVerificationStatus.APPROVED
        else DriverStatus.REJECTED
    )
    profile.save(update_fields=["status"])

    verification = DriverVerification.objects.create(
        admin=admin_user,
        driver=profile.user,
        status=status,
        notes=notes or "",
    )

    return DriverVerificationResult(verification=verification, profile=profile)


