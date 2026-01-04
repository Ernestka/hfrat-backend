"""Input validators and sanitizers."""
import re
from typing import Any, Dict, List


def sanitize_string(value: Any, max_length: int = 1000) -> str:
    """Sanitize string input to prevent injection attacks.

    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string, stripped and truncated
    """
    if value is None:
        return ""

    # Convert to string and strip whitespace
    sanitized = str(value).strip()

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def sanitize_email(email: Any) -> str:
    """Sanitize and validate email format.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email in lowercase
    """
    if not email:
        return ""

    # Basic sanitization
    sanitized = sanitize_string(email, max_length=255).lower()

    # Remove any dangerous characters
    sanitized = re.sub(r"[<>()\[\]{}|\\]", "", sanitized)

    return sanitized


def is_valid_email(email: str) -> bool:
    """Validate email format using regex.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid
    """
    if not email:
        return False

    # RFC 5322 simplified email regex
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def sanitize_integer(value: Any, min_val: int | None = None, max_val: int | None = None) -> int | None:
    """Sanitize and validate integer input.

    Args:
        value: Value to sanitize
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Sanitized integer or None if invalid
    """
    if value is None:
        return None

    try:
        num = int(value)

        if min_val is not None and num < min_val:
            return None
        if max_val is not None and num > max_val:
            return None

        return num
    except (TypeError, ValueError):
        return None


def validate_user_payload(data: Dict, require_password: bool = True) -> List[str]:
    """Validate user creation/update payload.

    Args:
        data: User data dictionary
        require_password: Whether password is required

    Returns:
        List of validation error messages
    """
    errors: List[str] = []

    # Sanitize and validate email
    email = sanitize_email(data.get("email"))

    if not email:
        errors.append("Email is required.")
    elif not is_valid_email(email):
        errors.append("Invalid email format.")
    elif len(email) > 255:
        errors.append("Email is too long (max 255 characters).")

    # Validate password
    password = data.get("password")
    if require_password and not password:
        errors.append("Password is required.")
    elif password:
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        elif len(password) > 128:
            errors.append("Password is too long (max 128 characters).")

    return errors


def validate_report_payload(data: Dict) -> List[str]:
    """Validate resource report payload.

    Args:
        data: Resource report data dictionary

    Returns:
        List of validation error messages
    """
    errors: List[str] = []

    # Validate facility_id
    facility_id = sanitize_integer(data.get("facility_id"), min_val=1)
    if facility_id is None:
        if data.get("facility_id") is None:
            errors.append("facility_id is required.")
        else:
            errors.append("facility_id must be a positive integer.")

    # Validate resource counts
    for field in ["icu_beds_available", "ventilators_available", "staff_on_duty"]:
        value = data.get(field)
        if value is None:
            errors.append(f"{field} is required.")
            continue

        sanitized = sanitize_integer(value, min_val=0, max_val=10000)
        if sanitized is None:
            if str(value).strip() == "":
                errors.append(f"{field} is required.")
            else:
                errors.append(
                    f"{field} must be a non-negative integer (max 10000).")

    return errors


def validate_facility_payload(data: Dict) -> List[str]:
    """Validate facility creation/update payload.

    Args:
        data: Facility data dictionary

    Returns:
        List of validation error messages
    """
    errors: List[str] = []

    # Validate name
    name = sanitize_string(data.get("name"), max_length=150)
    if not name:
        errors.append("Facility name is required.")
    elif len(name) < 2:
        errors.append("Facility name must be at least 2 characters.")

    # Validate optional fields
    if data.get("country"):
        country = sanitize_string(data.get("country"), max_length=120)
        if len(country) > 120:
            errors.append("Country name is too long (max 120 characters).")

    if data.get("city"):
        city = sanitize_string(data.get("city"), max_length=120)
        if len(city) > 120:
            errors.append("City name is too long (max 120 characters).")

    return errors
