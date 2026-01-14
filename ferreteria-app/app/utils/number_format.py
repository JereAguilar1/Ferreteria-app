"""Number parsing utilities for Argentine formats."""
import re
from decimal import Decimal, InvalidOperation

AR_DECIMAL_PATTERN = re.compile(r"^(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}$")


def parse_ar_decimal(value: str) -> Decimal:
    """
    Parse a monetary string in Argentine format (e.g., 1.234,56) to Decimal.

    Rules:
    - Thousands separator: dot (.)
    - Decimal separator: comma (,)
    - Exactly 2 decimal digits
    - No negatives
    - Proper thousand grouping (1.234,56 is valid; 1.2,00 is not)

    Raises:
        ValueError: if the value is invalid or empty.
    """
    if value is None:
        raise ValueError('Formato inválido. Usá 1.234,56')

    cleaned = value.strip()
    if not cleaned:
        raise ValueError('Formato inválido. Usá 1.234,56')

    if not AR_DECIMAL_PATTERN.match(cleaned):
        raise ValueError('Formato inválido. Usá 1.234,56')

    normalized = cleaned.replace('.', '').replace(',', '.')
    try:
        decimal_value = Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise ValueError('Formato inválido. Usá 1.234,56')

    if decimal_value < 0:
        raise ValueError('El valor no puede ser negativo')

    return decimal_value.quantize(Decimal('0.01'))
