#!/usr/bin/env python3
"""
Test script to verify PaymentMethod normalization fix.

This script tests:
1. Creating a quote with CASH payment method
2. Converting to sale
3. Verifying finance_ledger.payment_method is stored as 'CASH' string
4. Repeating with TRANSFER
"""

import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import (
    Quote, QuoteLine, Sale, FinanceLedger, Product, 
    PaymentMethod, normalize_payment_method
)
from app.services.quote_service import convert_quote_to_sale


def test_normalize_payment_method():
    """Test the normalize_payment_method helper."""
    print("\n" + "="*60)
    print("TEST 1: normalize_payment_method() helper")
    print("="*60)
    
    # Test with None
    result = normalize_payment_method(None)
    assert result == 'CASH', f"Expected 'CASH', got {result}"
    print("✅ None -> 'CASH'")
    
    # Test with PaymentMethod enum
    result = normalize_payment_method(PaymentMethod.CASH)
    assert result == 'CASH', f"Expected 'CASH', got {result}"
    print("✅ PaymentMethod.CASH -> 'CASH'")
    
    result = normalize_payment_method(PaymentMethod.TRANSFER)
    assert result == 'TRANSFER', f"Expected 'TRANSFER', got {result}"
    print("✅ PaymentMethod.TRANSFER -> 'TRANSFER'")
    
    # Test with string
    result = normalize_payment_method('cash')
    assert result == 'CASH', f"Expected 'CASH', got {result}"
    print("✅ 'cash' -> 'CASH'")
    
    result = normalize_payment_method('TRANSFER')
    assert result == 'TRANSFER', f"Expected 'TRANSFER', got {result}"
    print("✅ 'TRANSFER' -> 'TRANSFER'")
    
    # Test invalid
    try:
        normalize_payment_method('INVALID')
        print("❌ Should have raised ValueError for 'INVALID'")
        sys.exit(1)
    except ValueError as e:
        print(f"✅ 'INVALID' raises ValueError: {e}")
    
    print("\n✅ ALL normalize_payment_method() TESTS PASSED\n")


def test_quote_conversion_with_cash():
    """Test converting quote with CASH payment method."""
    print("\n" + "="*60)
    print("TEST 2: Convert Quote with CASH to Sale")
    print("="*60)
    
    session = SessionLocal()
    
    try:
        # Get a product
        product = session.query(Product).filter(Product.active == True).first()
        
        if not product:
            print("⚠️  No active products found. Skipping test.")
            return
        
        print(f"Using product: {product.name} (ID: {product.id})")
        
        # Create a test quote with CASH
        quote = Quote(
            quote_number=f'TEST-CASH-{int(datetime.now().timestamp())}',
            status='DRAFT',
            issued_at=datetime.now(),
            valid_until=(datetime.now() + timedelta(days=7)).date(),
            payment_method='CASH',
            customer_name='Test Customer CASH',
            total_amount=Decimal('100.00')
        )
        session.add(quote)
        session.flush()
        
        # Add a line
        quote_line = QuoteLine(
            quote_id=quote.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            uom_snapshot=product.uom.symbol if product.uom else 'UN',
            qty=Decimal('1.0'),
            unit_price=Decimal('100.00'),
            line_total=Decimal('100.00')
        )
        session.add(quote_line)
        session.commit()
        
        print(f"✅ Created quote #{quote.quote_number} with payment_method='CASH'")
        
        # Convert to sale
        quote_id = quote.id
        sale_id = convert_quote_to_sale(quote_id, session)
        
        print(f"✅ Converted to sale ID: {sale_id}")
        
        # Verify finance_ledger entry
        ledger = session.query(FinanceLedger).filter(
            FinanceLedger.reference_type == 'SALE',
            FinanceLedger.reference_id == sale_id
        ).first()
        
        if not ledger:
            print("❌ No finance_ledger entry found for sale")
            sys.exit(1)
        
        print(f"✅ Found finance_ledger entry (ID: {ledger.id})")
        print(f"   payment_method: {ledger.payment_method!r} (type: {type(ledger.payment_method).__name__})")
        
        # Critical assertion
        assert isinstance(ledger.payment_method, str), \
            f"payment_method should be str, got {type(ledger.payment_method).__name__}"
        assert ledger.payment_method == 'CASH', \
            f"payment_method should be 'CASH', got {ledger.payment_method!r}"
        
        print("✅ payment_method is correctly stored as 'CASH' string")
        print("\n✅ TEST 2 PASSED: CASH conversion works\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def test_quote_conversion_with_transfer():
    """Test converting quote with TRANSFER payment method."""
    print("\n" + "="*60)
    print("TEST 3: Convert Quote with TRANSFER to Sale")
    print("="*60)
    
    session = SessionLocal()
    
    try:
        # Get a product
        product = session.query(Product).filter(Product.active == True).first()
        
        if not product:
            print("⚠️  No active products found. Skipping test.")
            return
        
        print(f"Using product: {product.name} (ID: {product.id})")
        
        # Create a test quote with TRANSFER
        quote = Quote(
            quote_number=f'TEST-TRANSFER-{int(datetime.now().timestamp())}',
            status='DRAFT',
            issued_at=datetime.now(),
            valid_until=(datetime.now() + timedelta(days=7)).date(),
            payment_method='TRANSFER',
            customer_name='Test Customer TRANSFER',
            total_amount=Decimal('200.00')
        )
        session.add(quote)
        session.flush()
        
        # Add a line
        quote_line = QuoteLine(
            quote_id=quote.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            uom_snapshot=product.uom.symbol if product.uom else 'UN',
            qty=Decimal('2.0'),
            unit_price=Decimal('100.00'),
            line_total=Decimal('200.00')
        )
        session.add(quote_line)
        session.commit()
        
        print(f"✅ Created quote #{quote.quote_number} with payment_method='TRANSFER'")
        
        # Convert to sale
        quote_id = quote.id
        sale_id = convert_quote_to_sale(quote_id, session)
        
        print(f"✅ Converted to sale ID: {sale_id}")
        
        # Verify finance_ledger entry
        ledger = session.query(FinanceLedger).filter(
            FinanceLedger.reference_type == 'SALE',
            FinanceLedger.reference_id == sale_id
        ).first()
        
        if not ledger:
            print("❌ No finance_ledger entry found for sale")
            sys.exit(1)
        
        print(f"✅ Found finance_ledger entry (ID: {ledger.id})")
        print(f"   payment_method: {ledger.payment_method!r} (type: {type(ledger.payment_method).__name__})")
        
        # Critical assertion
        assert isinstance(ledger.payment_method, str), \
            f"payment_method should be str, got {type(ledger.payment_method).__name__}"
        assert ledger.payment_method == 'TRANSFER', \
            f"payment_method should be 'TRANSFER', got {ledger.payment_method!r}"
        
        print("✅ payment_method is correctly stored as 'TRANSFER' string")
        print("\n✅ TEST 3 PASSED: TRANSFER conversion works\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ TEST 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def main():
    """Run all tests."""
    print("\n" + "🧪"*30)
    print(" PAYMENT METHOD NORMALIZATION FIX - VERIFICATION TESTS")
    print("🧪"*30)
    
    try:
        test_normalize_payment_method()
        test_quote_conversion_with_cash()
        test_quote_conversion_with_transfer()
        
        print("\n" + "✅"*30)
        print(" ALL TESTS PASSED - Fix is working correctly!")
        print("✅"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
