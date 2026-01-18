"""
Utilidad para parsear decimales en formato argentino.
Maneja conversión segura de strings con formato AR a Decimal.
"""
from decimal import Decimal, InvalidOperation
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


def parse_decimal_ar(
    raw: Union[str, int, float, Decimal, None],
    default: Union[str, int, float, Decimal] = "0",
    field_name: str = "unknown"
) -> Decimal:
    """
    Parsea un valor numérico que puede venir en formato argentino o normalizado.
    
    Formatos aceptados:
    - "1.234,56" (argentino: miles con punto, decimal con coma)
    - "1234.56" (normalizado: decimal con punto)
    - "1234" (entero)
    - "" / None (retorna default)
    - 1234 (int)
    - 1234.56 (float)
    - Decimal("1234.56")
    
    Args:
        raw: Valor a parsear
        default: Valor por defecto si raw es None o vacío
        field_name: Nombre del campo (para logging)
    
    Returns:
        Decimal parseado
    
    Raises:
        ValueError: Si el valor no es parseable
    
    Examples:
        parse_decimal_ar("1.234,56") -> Decimal("1234.56")
        parse_decimal_ar("1234.56") -> Decimal("1234.56")
        parse_decimal_ar("") -> Decimal("0")
        parse_decimal_ar(None, "10") -> Decimal("10")
    """
    # Si ya es Decimal, retornar directamente
    if isinstance(raw, Decimal):
        return raw
    
    # Si es None o string vacío, usar default
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        try:
            return Decimal(str(default))
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Invalid default value for field '{field_name}': {repr(default)}")
            raise ValueError(f"Invalid default value for {field_name}: {default}") from e
    
    # Si es int o float, convertir directamente
    if isinstance(raw, (int, float)):
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Cannot convert numeric value for field '{field_name}': {repr(raw)}")
            raise ValueError(f"Invalid numeric value for {field_name}: {raw}") from e
    
    # Debe ser string en este punto
    if not isinstance(raw, str):
        logger.error(f"Unexpected type for field '{field_name}': {type(raw).__name__}, value: {repr(raw)}")
        raise ValueError(f"Invalid type for {field_name}: expected string, got {type(raw).__name__}")
    
    # Limpiar el string
    value = raw.strip()
    
    if value == "":
        try:
            return Decimal(str(default))
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Invalid default value for field '{field_name}': {repr(default)}")
            raise ValueError(f"Invalid default value for {field_name}: {default}") from e
    
    # Detectar y normalizar formato argentino
    # Formato AR: "1.234,56" -> "1234.56"
    # Formato normalizado: "1234.56" -> "1234.56"
    
    # Contar puntos y comas
    num_dots = value.count('.')
    num_commas = value.count(',')
    
    try:
        # Caso 1: Formato argentino con miles y decimal: "1.234,56"
        if num_dots > 0 and num_commas == 1:
            # Quitar puntos (separador de miles) y cambiar coma por punto
            normalized = value.replace('.', '').replace(',', '.')
            return Decimal(normalized)
        
        # Caso 2: Solo coma (decimal argentino sin miles): "1234,56"
        elif num_commas == 1 and num_dots == 0:
            normalized = value.replace(',', '.')
            return Decimal(normalized)
        
        # Caso 3: Solo punto (puede ser miles o decimal normalizado)
        elif num_dots == 1 and num_commas == 0:
            # Si tiene más de 3 dígitos después del punto, es separador de miles
            parts = value.split('.')
            if len(parts) == 2 and len(parts[1]) > 2:
                # Es separador de miles: "1.234" -> "1234"
                normalized = value.replace('.', '')
            else:
                # Es decimal normalizado: "1234.56" -> "1234.56"
                normalized = value
            return Decimal(normalized)
        
        # Caso 4: Múltiples puntos (separadores de miles): "1.234.567"
        elif num_dots > 1 and num_commas == 0:
            normalized = value.replace('.', '')
            return Decimal(normalized)
        
        # Caso 5: Sin puntos ni comas (entero simple): "1234"
        elif num_dots == 0 and num_commas == 0:
            return Decimal(value)
        
        # Caso 6: Formato inválido
        else:
            logger.error(
                f"Invalid decimal format for field '{field_name}': {repr(value)} "
                f"(dots: {num_dots}, commas: {num_commas})"
            )
            raise ValueError(
                f"Invalid decimal format for {field_name}: '{value}'. "
                f"Expected formats: '1234.56', '1.234,56', '1234', or '1234,56'"
            )
    
    except (InvalidOperation, ValueError) as e:
        logger.error(
            f"Failed to parse decimal for field '{field_name}': {repr(value)} - {str(e)}"
        )
        raise ValueError(
            f"Cannot parse decimal value for {field_name}: '{value}'. "
            f"Expected a valid number."
        ) from e


def parse_decimal_ar_safe(
    raw: Union[str, int, float, Decimal, None],
    default: Union[str, int, float, Decimal] = "0",
    field_name: str = "unknown"
) -> Decimal:
    """
    Versión segura de parse_decimal_ar que nunca lanza excepciones.
    Retorna el default si hay cualquier error.
    
    Args:
        raw: Valor a parsear
        default: Valor por defecto
        field_name: Nombre del campo (para logging)
    
    Returns:
        Decimal parseado o default
    """
    try:
        return parse_decimal_ar(raw, default, field_name)
    except (ValueError, InvalidOperation) as e:
        logger.warning(f"Failed to parse {field_name}, using default: {e}")
        try:
            return Decimal(str(default))
        except:
            return Decimal("0")
