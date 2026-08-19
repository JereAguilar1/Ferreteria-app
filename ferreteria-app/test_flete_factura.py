#!/usr/bin/env python3
import os
import sys
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.purchase_invoice import PurchaseInvoice
from app.database import get_session

def main():
    print("\n" + "="*60)
    print("TEST: Factura Flete (Shipping Cost) Database & Models")
    print("="*60)
    
    app = create_app('config.Config')
    
    with app.app_context():
        db_session = get_session()
        try:
            # Attempt to create an invoice with shipping_cost
            invoice = PurchaseInvoice(
                supplier_id=1,
                invoice_number='TEST-FLETE-1',
                shipping_cost=Decimal('25.50'),
                total=Decimal('125.50')
            )
            print("✅ Model accepts shipping_cost attribute")
            
            db_session.add(invoice)
            db_session.flush()
            
            if invoice.shipping_cost == Decimal('25.50'):
                print("✅ Database stores shipping_cost correctly")
            else:
                raise Exception("Database did not return the expected shipping_cost")
            
            print("\n✅ ALL DB/MODEL TESTS PASSED\n")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}\n")
            sys.exit(1)
        finally:
            db_session.rollback()
            db_session.remove()

if __name__ == '__main__':
    main()
