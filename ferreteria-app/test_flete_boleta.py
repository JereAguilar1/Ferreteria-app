#!/usr/bin/env python3
import os
import sys
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.sale import Sale
from app.models.product import Product
from app.models.uom import UOM
from app.services.sales_service import confirm_sale
from app.database import get_session
from sqlalchemy.exc import ArgumentError

def main():
    print("\n" + "="*60)
    print("TEST: Boleta Flete (Shipping Cost) Backend Logic")
    print("="*60)
    
    app = create_app('config.Config')
    
    with app.app_context():
        db_session = get_session()
        try:
            # Find a product and UOM
            product = db_session.query(Product).first()
            uom = db_session.query(UOM).first()
            if not product or not uom:
                print("⚠️ No products or UOM found, skipping test")
                return

            cart = {
                'items': {
                    f"{product.id}_{uom.id}": {
                        'qty': '2',
                        'qty_base': '2',
                        'product_id': product.id,
                        'uom_id': uom.id,
                        'uom_name': uom.name,
                        'unit_price': '10.00'
                    }
                }
            }
            
            # The signature of confirm_sale should accept shipping_cost
            sale_id = confirm_sale(cart, db_session, payment_method='CASH', shipping_cost=Decimal('15.00'))
            sale = db_session.query(Sale).get(sale_id)
            if sale.shipping_cost == Decimal('15.00') and sale.total == Decimal('35.00'):
                print("✅ Backend service calculates total correctly.")
            else:
                raise Exception(f"Incorrect total or shipping cost: {sale.total}, {sale.shipping_cost}")
            
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
