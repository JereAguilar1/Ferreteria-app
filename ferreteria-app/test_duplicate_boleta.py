#!/usr/bin/env python3
"""
Test script to verify Boleta Duplication logic.

This script tests:
1. Creating a boleta with products.
2. Making a POST request to /invoices/<id>/duplicate.
3. Verifying the session draft is populated with the correct data.
"""

import os
import sys
from decimal import Decimal
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.database import SessionLocal
from app.models import PurchaseInvoice, PurchaseInvoiceLine, Supplier, Product
from app.utils.formatters import get_now_ar


def main():
    print("\n" + "="*60)
    print("TEST: Duplicate Boleta (Invoice) Data Transformation")
    print("="*60)
    
    app = create_app('config.Config')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    
    db_session = SessionLocal()
    
    try:
        # Prepare test data
        supplier = db_session.query(Supplier).first()
        if not supplier:
            supplier = Supplier(name="Test Supplier Duplication", document_number="1234")
            db_session.add(supplier)
            db_session.flush()
            
        product = db_session.query(Product).first()
        if not product:
            print("⚠️ No active products found. Please ensure seed data is run.")
            return

        today = get_now_ar().date()
        
        # 1. Create a test boleta
        invoice = PurchaseInvoice(
            supplier_id=supplier.id,
            invoice_number='INV-DUPLICATE-TEST',
            invoice_date=today,
            total_amount=Decimal('500.00'),
            status='PENDING'
        )
        db_session.add(invoice)
        db_session.flush()
        
        line = PurchaseInvoiceLine(
            invoice_id=invoice.id,
            product_id=product.id,
            qty=Decimal('5.0'),
            unit_cost=Decimal('100.00'),
            vat_rate=Decimal('21.0'),
            vat_amount=Decimal('105.00'),
            net_amount=Decimal('500.00'),
            line_total=Decimal('605.00')
        )
        db_session.add(line)
        db_session.commit()
        
        invoice_id = invoice.id
        supplier_id = supplier.id
        product_id = product.id
        
        print(f"✅ Created test boleta ID: {invoice_id}")
        
        # 2. Make POST request to duplicate endpoint
        with app.test_client() as client:
            response = client.post(f'/invoices/{invoice_id}/duplicate')
            
            # 3. Verify redirects to /new
            assert response.status_code == 302, f"Expected redirect, got {response.status_code}"
            assert '/invoices/new' in response.headers['Location'], f"Expected redirect to /new, got {response.headers['Location']}"
            print("✅ Redirects to /invoices/new")
            
            # 4. Verify session draft
            with client.session_transaction() as sess:
                draft = sess.get('invoice_draft')
                assert draft is not None, "invoice_draft not in session"
                
                assert draft['supplier_id'] == supplier_id, f"Expected supplier_id {supplier_id}, got {draft['supplier_id']}"
                assert draft['invoice_number'] == '', "invoice_number should be empty"
                assert draft['invoice_date'] == today.strftime('%Y-%m-%d'), "invoice_date should be today"
                
                assert len(draft['lines']) == 1, "Should have 1 line"
                assert draft['lines'][0]['product_id'] == product_id, "Product ID mismatch"
                assert draft['lines'][0]['qty'] == 5.0, "Quantity mismatch"
                assert draft['lines'][0]['unit_cost'] == 100.0, "Unit cost mismatch"
                assert draft['lines'][0]['vat_rate'] == 21.0, "VAT rate mismatch"
                
                print("✅ Session draft successfully populated with transformed data!")
                print("\n✅ ALL TESTS PASSED\n")

    except Exception as e:
        db_session.rollback()
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db_session.close()

if __name__ == '__main__':
    main()
