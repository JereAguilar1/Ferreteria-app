#!/usr/bin/env python3
import os
import sys
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models.sale import Sale
from sqlalchemy.exc import ArgumentError

def main():
    print("\n" + "="*60)
    print("TEST: Boleta Flete (Shipping Cost) Model Attribute")
    print("="*60)
    
    app = create_app('config.Config')
    
    try:
        # Create a Sale object with shipping_cost
        sale = Sale(
            total=Decimal('100.00'),
            shipping_cost=Decimal('50.00')
        )
        
        # This will fail in Red Phase because shipping_cost does not exist on Sale model yet
        if hasattr(sale, 'shipping_cost') and sale.shipping_cost == Decimal('50.00'):
            print("✅ Sale model correctly accepts shipping_cost.")
        else:
            raise Exception("Sale model does not have shipping_cost attribute correctly set.")
            
        print("\n✅ ALL MODEL TESTS PASSED\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED (Expected during Red Phase): {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
