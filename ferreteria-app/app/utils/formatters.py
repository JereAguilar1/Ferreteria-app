"""
Utilidades de formateo para templates.
Incluye formatos de números, fechas y otros en estilo argentino.
"""
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Union, Optional
from zoneinfo import ZoneInfo


def to_argentina(dt: Union[datetime, None]) -> Union[datetime, None]:
    """
    Convierte un datetime a la zona horaria de Argentina.
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
    
    Returns:
        Datetime en zona horaria Argentina o None si el input es None
    
    Examples:
        to_argentina(datetime(2026, 1, 18, 10, 0, tzinfo=UTC)) 
        -> datetime(2026, 1, 18, 7, 0, tzinfo=ZoneInfo('America/Argentina/Buenos_Aires'))
    """
    if dt is None:
        return None
    
    if not isinstance(dt, datetime):
        return None
    
    # Si el datetime es naive (sin timezone), asumimos UTC
    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convertir a zona horaria argentina
    return dt.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))


def num_ar(value: Union[int, float, Decimal, str, None], decimals: Optional[int] = None) -> str:
    """
    Formatea un número en estilo argentino:
    - Separador de miles: punto (.)
    - Separador decimal: coma (,)
    - Si no tiene decimales significativos, no los muestra
    
    Args:
        value: Número a formatear
        decimals: Cantidad fija de decimales (None = automático)
    
    Returns:
        String formateado
    
    Examples:
        num_ar(1500) -> "1.500"
        num_ar(1500.5) -> "1.500,5"
        num_ar(1500.75) -> "1.500,75"
        num_ar(185.00) -> "185"
        num_ar(100550.00) -> "100.550"
        num_ar(None) -> "-"
    """
    if value is None or value == "":
        return "-"
    
    try:
        # Convertir a Decimal para precisión
        if isinstance(value, str):
            value = value.replace(",", ".")
        num = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "-"
    
    # Si es cero
    if num == 0:
        return "0"
    
    # Determinar si tiene decimales significativos
    if decimals is not None:
        # Decimales fijos
        num = num.quantize(Decimal(10) ** -decimals)
    
    # Separar parte entera y decimal
    sign, digits, exponent = num.as_tuple()
    
    # Construir número como string sin notación científica
    num_str = str(num)
    
    # Separar parte entera y decimal
    if '.' in num_str:
        integer_part, decimal_part = num_str.split('.')
        # Eliminar ceros finales en decimales
        decimal_part = decimal_part.rstrip('0')
    else:
        integer_part = num_str
        decimal_part = ""
    
    # Manejar signo negativo
    if integer_part.startswith('-'):
        sign_str = '-'
        integer_part = integer_part[1:]
    else:
        sign_str = ''
    
    # Agregar separador de miles (punto)
    # Revertir, agrupar de 3, revertir de nuevo
    reversed_int = integer_part[::-1]
    groups = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
    integer_formatted = '.'.join(groups)[::-1]
    
    # Construir resultado
    if decimal_part:
        return f"{sign_str}{integer_formatted},{decimal_part}"
    else:
        return f"{sign_str}{integer_formatted}"


def money_ar(value: Union[int, float, Decimal, str, None]) -> str:
    """
    Formatea un monto monetario en estilo argentino.
    Alias de num_ar específico para dinero.
    
    Args:
        value: Monto a formatear
    
    Returns:
        String formateado
    
    Examples:
        money_ar(1500.00) -> "1.500"
        money_ar(1500.50) -> "1.500,5"
        money_ar(1500.75) -> "1.500,75"
    """
    return num_ar(value)


def money_ar_2(value: Union[int, float, Decimal, str, None]) -> str:
    """
    Formatea un monto monetario en estilo argentino con exactamente 2 decimales.
    Siempre muestra dos decimales y usa punto para miles y coma para decimales.

    Args:
        value: Monto a formatear

    Returns:
        String formateado (ej: 1.500,00). Devuelve "-" si es inválido.
    """
    if value is None or value == "":
        return "-"

    try:
        normalized = str(value).replace(",", ".")
        num = Decimal(normalized).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        return "-"

    sign = "-" if num < 0 else ""
    num = abs(num)

    integer_part, decimal_part = f"{num:.2f}".split(".")
    reversed_int = integer_part[::-1]
    groups = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
    integer_formatted = '.'.join(groups)[::-1]

    return f"{sign}{integer_formatted},{decimal_part}"


def date_ar(value: Union[date, datetime, None]) -> str:
    """
    Formatea una fecha en formato argentino: DD/MM/YYYY
    
    Args:
        value: Fecha a formatear
    
    Returns:
        String formateado o "-" si es None
    
    Examples:
        date_ar(date(2026, 1, 12)) -> "12/01/2026"
    """
    if value is None:
        return "-"
    
    if isinstance(value, datetime):
        value = value.date()
    
    if not isinstance(value, date):
        return "-"
    
    return value.strftime("%d/%m/%Y")


def datetime_ar(value: Union[datetime, None], with_time: bool = True) -> str:
    """
    Formatea un datetime en formato argentino: DD/MM/YYYY HH:MM
    Convierte automáticamente a zona horaria de Argentina antes de formatear.
    
    Args:
        value: Datetime a formatear (puede ser naive o aware)
        with_time: Si True, incluye hora. Si False, solo fecha.
    
    Returns:
        String formateado o "-" si es None
    
    Examples:
        datetime_ar(datetime(2026, 1, 12, 15, 30, tzinfo=UTC)) -> "12/01/2026 12:30" (Argentina UTC-3)
        datetime_ar(datetime(2026, 1, 12, 15, 30), with_time=False) -> "12/01/2026"
    """
    if value is None:
        return "-"
    
    if not isinstance(value, datetime):
        return "-"
    
    # Convertir a zona horaria argentina
    value_ar = to_argentina(value)
    if value_ar is None:
        return "-"
    
    if with_time:
        return value_ar.strftime("%d/%m/%Y %H:%M")
    else:
        return value_ar.strftime("%d/%m/%Y")


def month_ar(value: Union[datetime, None]) -> str:
    """
    Formatea un periodo mensual en formato MM/YYYY
    
    Args:
        value: Datetime representando el mes
    
    Returns:
        String formateado o "-" si es None
    
    Examples:
        month_ar(datetime(2026, 1, 1)) -> "01/2026"
    """
    if value is None:
        return "-"
    
    if not isinstance(value, datetime):
        return "-"
    
    return value.strftime("%m/%Y")


def year_ar(value: Union[datetime, int, None]) -> str:
    """
    Formatea un año en formato YYYY
    
    Args:
        value: Datetime o int representando el año
    
    Returns:
        String formateado o "-" si es None
    
    Examples:
        year_ar(datetime(2026, 1, 1)) -> "2026"
        year_ar(2026) -> "2026"
    """
    if value is None:
        return "-"
    
    if isinstance(value, int):
        return str(value)
    
    if isinstance(value, datetime):
        return value.strftime("%Y")
    
    return "-"

def num_ar(value, decimals=2):
    """
    Formatea un número en formato argentino.
    
    Args:
        value: Número a formatear (int, float, Decimal, str)
        decimals: Número de decimales a mostrar (default: 2)
    
    Returns:
        String formateado en formato AR (1.234,56) o "0,00" si hay error
    
    Examples:
        num_ar(1234.56) -> "1.234,56"
        num_ar(1234.567, 3) -> "1.234,567"
        num_ar(1500) -> "1.500,00"
    """
    try:
        value = float(value)
        # Format with specified decimals
        formatted = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (TypeError, ValueError):
        # Return default with specified decimals
        return "0" + ("," + "0" * decimals if decimals > 0 else "")