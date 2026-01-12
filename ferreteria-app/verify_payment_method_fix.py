"""
Quick verification that payment_method normalization is working.
Run inside Docker: docker compose exec web python verify_payment_method_fix.py
"""

from app.models import PaymentMethod, normalize_payment_method

print("\n" + "="*60)
print("🧪 TESTING normalize_payment_method() HELPER")
print("="*60 + "\n")

# Test 1: None -> CASH
result = normalize_payment_method(None)
print(f"✅ normalize_payment_method(None) = {result!r}")
assert result == 'CASH'

# Test 2: PaymentMethod.CASH (Enum) -> 'CASH' (string)
result = normalize_payment_method(PaymentMethod.CASH)
print(f"✅ normalize_payment_method(PaymentMethod.CASH) = {result!r}")
assert result == 'CASH'
assert isinstance(result, str)

# Test 3: PaymentMethod.TRANSFER (Enum) -> 'TRANSFER' (string)
result = normalize_payment_method(PaymentMethod.TRANSFER)
print(f"✅ normalize_payment_method(PaymentMethod.TRANSFER) = {result!r}")
assert result == 'TRANSFER'
assert isinstance(result, str)

# Test 4: String 'cash' -> 'CASH'
result = normalize_payment_method('cash')
print(f"✅ normalize_payment_method('cash') = {result!r}")
assert result == 'CASH'

# Test 5: String 'TRANSFER' -> 'TRANSFER'
result = normalize_payment_method('TRANSFER')
print(f"✅ normalize_payment_method('TRANSFER') = {result!r}")
assert result == 'TRANSFER'

# Test 6: Invalid value raises ValueError
try:
    normalize_payment_method('INVALID')
    print("❌ Should have raised ValueError")
    exit(1)
except ValueError as e:
    print(f"✅ normalize_payment_method('INVALID') raises ValueError: {e}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - normalize_payment_method() works!")
print("="*60 + "\n")

print("📋 Summary:")
print("   - Enum values are correctly converted to strings")
print("   - String values are normalized to uppercase")
print("   - None defaults to 'CASH'")
print("   - Invalid values raise ValueError")
print("\n✅ The fix prevents psycopg2.ProgrammingError for Enum types\n")
