import re
from decimal import Decimal
from django import template

register = template.Library()


@register.filter(name="inr")
def inr(value):
    """
    Formats a number into the Indian currency format (e.g., ₹1,50,000 or ₹12,34,567.89).
    """
    if value is None or value == "":
        return "₹0"
    try:
        val = Decimal(str(value))
    except Exception:
        return f"₹{value}"

    is_negative = val < 0
    val = abs(val)

    # Format to two decimal places
    s = f"{val:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # In Indian system, after the last 3 digits, groups of 2 digits are separated by commas
        remaining_parts = []
        while len(remaining) > 2:
            remaining_parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            remaining_parts.insert(0, remaining)
        formatted_int = ",".join(remaining_parts) + "," + last_three

    res = f"₹{formatted_int}"
    if decimal_part != "00":
        res += f".{decimal_part}"
    if is_negative:
        res = f"-{res}"
    return res


@register.filter(name="mask_phone")
def mask_phone(phone):
    """
    Masks mobile number for privacy compliance: e.g., 9876543210 -> 98******10
    """
    if not phone or len(str(phone)) < 6:
        return "******"
    p = str(phone).strip()
    return f"{p[:2]}******{p[-2:]}"


@register.filter(name="percentage_of")
def percentage_of(part, total):
    """
    Calculates percentage safely without division by zero.
    """
    try:
        p = float(part or 0)
        t = float(total or 0)
        if t <= 0:
            return 0
        return min(100, round((p / t) * 100))
    except Exception:
        return 0
