"""Script to seed initial data (UOM and Categories)."""
from app import create_app
from app.database import get_session
from app.models import UOM, Category

def seed_data():
    """Insert initial UOM and Category data if tables are empty."""
    app = create_app()
    
    with app.app_context():
        session = get_session()
        
        try:
            # Check if UOM table is empty
            uom_count = session.query(UOM).count()
            if uom_count == 0:
                print("Inserting initial UOM (Units of Measure)...")
                uoms = [
                    UOM(name='Unidad', symbol='UN'),
                    UOM(name='Metro', symbol='M'),
                    UOM(name='Kilogramo', symbol='KG'),
                    UOM(name='Litro', symbol='L'),
                    UOM(name='Caja', symbol='CAJA'),
                    UOM(name='Bolsa', symbol='BOLSA'),
                    UOM(name='Metro cuadrado', symbol='M²'),
                    UOM(name='Paquete', symbol='PAQ'),
                ]
                session.add_all(uoms)
                session.commit()
                print(f"[OK] Inserted {len(uoms)} UOM records")
            else:
                print(f"UOM table already has {uom_count} records. Skipping.")
            
            # Check if Category table is empty
            category_count = session.query(Category).count()
            if category_count == 0:
                print("\nInserting initial Categories...")
                categories = [
                    Category(name='Herramientas'),
                    Category(name='Materiales de construccion'),
                    Category(name='Electricidad'),
                    Category(name='Plomeria'),
                    Category(name='Pintura'),
                    Category(name='Ferreteria general'),
                ]
                session.add_all(categories)
                session.commit()
                print(f"[OK] Inserted {len(categories)} Category records")
            else:
                print(f"Category table already has {category_count} records. Skipping.")
            
            print("\n[SUCCESS] Seed data completed successfully!")
            
        except Exception as e:
            session.rollback()
            print(f"\n[ERROR] Error seeding data: {e}")
            raise
        finally:
            session.close()


if __name__ == '__main__':
    seed_data()

