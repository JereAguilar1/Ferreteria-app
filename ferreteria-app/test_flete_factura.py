#!/usr/bin/env python3
import os
import sys
from decimal import Decimal
from datetime import date

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.purchase_invoice import PurchaseInvoice
from app.models.product import Product
from app.models.supplier import Supplier
from app.database import get_session
from app.services.invoice_service import create_invoice_with_lines

def main():
    print("\n" + "="*60)
    print("TEST: Factura Flete (Shipping Cost) Backend Logic")
    print("="*60)
    
    app = create_app('config.Config')
    
    with app.app_context():
        db_session = get_session()
        try:
            # We need a supplier and a product
            supplier = db_session.query(Supplier).first()
            product = db_session.query(Product).first()
            
            if not supplier or not product:
                print("⚠️ No supplier or product found, skipping test")
                return

            payload = {
                'supplier_id': supplier.id,
                'invoice_number': f'TEST-FLETE-{os.urandom(4).hex()}',
                'invoice_date': date.today(),
                'due_date': None,
                'shipping_cost': Decimal('100.00'),
                'lines': [
                    {
                        'product_id': product.id,
                        'qty': Decimal('2'),
                        'unit_cost': Decimal('50.00')
                    }
                ]
            }
            
            # This should calculate total as 2 * 50 + 100 = 200.00
            invoice_id = create_invoice_with_lines(payload, db_session)
            
            invoice = db_session.query(PurchaseInvoice).get(invoice_id)
            if invoice.shipping_cost == Decimal('100.00') and invoice.total_amount == Decimal('200.00'):
                print("✅ Backend service calculates invoice total correctly.")
            else:
                raise Exception(f"Incorrect total or shipping cost: {invoice.total_amount}, {invoice.shipping_cost}")
            
            print("\n✅ ALL BACKEND LOGIC TESTS PASSED\n")
            
        except Exception as e:
            db_session.rollback()
            print(f"\n❌ TEST FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            db_session.remove()

if __name__ == '__main__':
    main()
