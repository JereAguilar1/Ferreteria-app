"""
Seed script to populate database with sample data for testing.
Adds:
- 5 suppliers
- ~100 products
- Several purchase invoices with lines (increases stock)
- Some sales (decreases stock)
- Finance ledger entries
"""
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import random


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round decimal to match PostgreSQL's round() function."""
    quantizer = Decimal('0.1') ** places
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)

from app.database import get_session
from app.models import (
    Supplier, Product, Category, UOM, ProductStock,
    PurchaseInvoice, PurchaseInvoiceLine,
    Sale, SaleLine,
    StockMove, StockMoveLine,
    FinanceLedger
)
from app import create_app


def seed_suppliers(session):
    """Create 5 sample suppliers."""
    print("\n" + "="*60)
    print("INSERTING SUPPLIERS")
    print("="*60)
    
    suppliers_data = [
        {
            'name': 'Ferretería Mayorista del Norte',
            'tax_id': '30-12345678-9',
            'phone': '+54 11 4567-8901',
            'email': 'ventas@ferreterianorte.com.ar',
            'notes': 'Proveedor principal de herramientas y materiales de construcción'
        },
        {
            'name': 'Distribuidora Tornillos SA',
            'tax_id': '30-23456789-0',
            'phone': '+54 11 4567-8902',
            'email': 'pedidos@tornillos.com.ar',
            'notes': 'Especialista en tornillería y bulonería'
        },
        {
            'name': 'Pinturas Industriales SRL',
            'tax_id': '30-34567890-1',
            'phone': '+54 11 4567-8903',
            'email': 'comercial@pinturasindustriales.com.ar',
            'notes': 'Pinturas, barnices y productos químicos'
        },
        {
            'name': 'Herramientas y Máquinas del Sur',
            'tax_id': '30-45678901-2',
            'phone': '+54 11 4567-8904',
            'email': 'info@herramientasdelsur.com.ar',
            'notes': 'Herramientas eléctricas y manuales de alta gama'
        },
        {
            'name': 'Materiales de Construcción Oeste',
            'tax_id': '30-56789012-3',
            'phone': '+54 11 4567-8905',
            'email': 'ventas@materialesoeste.com.ar',
            'notes': 'Materiales de construcción y sanitarios'
        }
    ]
    
    suppliers = []
    for data in suppliers_data:
        supplier = Supplier(**data)
        session.add(supplier)
        suppliers.append(supplier)
    
    session.commit()
    print(f"✅ Inserted {len(suppliers)} suppliers")
    return suppliers


def seed_products(session):
    """Create ~100 sample products."""
    print("\n" + "="*60)
    print("INSERTING PRODUCTS")
    print("="*60)
    
    # Get UOMs and Categories
    uom_unidad = session.query(UOM).filter_by(name='Unidad').first()
    uom_kg = session.query(UOM).filter_by(name='Kilogramo').first()
    uom_metro = session.query(UOM).filter_by(name='Metro').first()
    uom_litro = session.query(UOM).filter_by(name='Litro').first()
    uom_caja = session.query(UOM).filter_by(name='Caja').first()
    uom_paquete = session.query(UOM).filter_by(name='Paquete').first()
    
    cat_herramientas = session.query(Category).filter_by(name='Herramientas').first()
    cat_construccion = session.query(Category).filter_by(name='Construcción').first()
    cat_electricidad = session.query(Category).filter_by(name='Electricidad').first()
    cat_pintura = session.query(Category).filter_by(name='Pintura').first()
    cat_plomeria = session.query(Category).filter_by(name='Plomería').first()
    cat_jardineria = session.query(Category).filter_by(name='Jardinería').first()
    
    products_data = [
        # HERRAMIENTAS (25 productos)
        ('MART-001', '7890001000001', 'Martillo Carpintero 16oz', cat_herramientas, uom_unidad, 1250.00),
        ('MART-002', '7890001000002', 'Martillo Bola 500g', cat_herramientas, uom_unidad, 980.00),
        ('DEST-001', '7890001000003', 'Destornillador Plano 6"', cat_herramientas, uom_unidad, 450.00),
        ('DEST-002', '7890001000004', 'Destornillador Phillips 6"', cat_herramientas, uom_unidad, 450.00),
        ('DEST-003', '7890001000005', 'Set Destornilladores 6pz', cat_herramientas, uom_caja, 2800.00),
        ('PINZ-001', '7890001000006', 'Pinza Universal 8"', cat_herramientas, uom_unidad, 1850.00),
        ('PINZ-002', '7890001000007', 'Pinza Corte 6"', cat_herramientas, uom_unidad, 1650.00),
        ('PINZ-003', '7890001000008', 'Pinza Punta 6"', cat_herramientas, uom_unidad, 1550.00),
        ('LLAV-001', '7890001000009', 'Llave Inglesa 10"', cat_herramientas, uom_unidad, 2450.00),
        ('LLAV-002', '7890001000010', 'Llave Francesa 12"', cat_herramientas, uom_unidad, 2850.00),
        ('LLAV-003', '7890001000011', 'Set Llaves Allen 9pz', cat_herramientas, uom_caja, 1950.00),
        ('SERR-001', '7890001000012', 'Serrucho Carpintero 18"', cat_herramientas, uom_unidad, 3250.00),
        ('SERR-002', '7890001000013', 'Sierra Arco Metal', cat_herramientas, uom_unidad, 1850.00),
        ('TALADRO-001', '7890001000014', 'Taladro Percutor 650W', cat_herramientas, uom_unidad, 18500.00),
        ('TALADRO-002', '7890001000015', 'Taladro Atornillador 12V', cat_herramientas, uom_unidad, 15800.00),
        ('AMOL-001', '7890001000016', 'Amoladora Angular 4½" 900W', cat_herramientas, uom_unidad, 22500.00),
        ('CIRC-001', '7890001000017', 'Sierra Circular 7¼" 1200W', cat_herramientas, uom_unidad, 28900.00),
        ('NIVEL-001', '7890001000018', 'Nivel Aluminio 60cm', cat_herramientas, uom_unidad, 3850.00),
        ('NIVEL-002', '7890001000019', 'Nivel Torpedo 25cm', cat_herramientas, uom_unidad, 1450.00),
        ('CINTA-001', '7890001000020', 'Cinta Métrica 5m', cat_herramientas, uom_unidad, 850.00),
        ('CINTA-002', '7890001000021', 'Cinta Métrica 8m', cat_herramientas, uom_unidad, 1250.00),
        ('ESCUADRA-001', '7890001000022', 'Escuadra Carpintero 30cm', cat_herramientas, uom_unidad, 2150.00),
        ('CEPILLO-001', '7890001000023', 'Cepillo Carpintero N°4', cat_herramientas, uom_unidad, 8500.00),
        ('FORMÓN-001', '7890001000024', 'Set Formones 6pz', cat_herramientas, uom_caja, 4850.00),
        ('TENAZA-001', '7890001000025', 'Tenaza Carpintero 8"', cat_herramientas, uom_unidad, 2250.00),
        
        # CONSTRUCCIÓN (25 productos)
        ('CEM-001', '7890002000001', 'Cemento Portland 50kg', cat_construccion, uom_kg, 4500.00),
        ('CAL-001', '7890002000002', 'Cal Hidratada 25kg', cat_construccion, uom_kg, 1850.00),
        ('YESO-001', '7890002000003', 'Yeso Bolsa 25kg', cat_construccion, uom_kg, 2150.00),
        ('ARENA-001', '7890002000004', 'Arena Fina Bolsa 30kg', cat_construccion, uom_kg, 1250.00),
        ('ARENA-002', '7890002000005', 'Arena Gruesa Bolsa 30kg', cat_construccion, uom_kg, 1150.00),
        ('LADR-001', '7890002000006', 'Ladrillo Común', cat_construccion, uom_unidad, 180.00),
        ('LADR-002', '7890002000007', 'Ladrillo Hueco 8cm', cat_construccion, uom_unidad, 220.00),
        ('LADR-003', '7890002000008', 'Ladrillo Hueco 12cm', cat_construccion, uom_unidad, 280.00),
        ('LADR-004', '7890002000009', 'Ladrillo Hueco 18cm', cat_construccion, uom_unidad, 350.00),
        ('BLOQ-001', '7890002000010', 'Bloque Hormigón 12cm', cat_construccion, uom_unidad, 450.00),
        ('BLOQ-002', '7890002000011', 'Bloque Hormigón 19cm', cat_construccion, uom_unidad, 620.00),
        ('HIERRO-001', '7890002000012', 'Hierro 6mm Barra 12m', cat_construccion, uom_unidad, 3850.00),
        ('HIERRO-002', '7890002000013', 'Hierro 8mm Barra 12m', cat_construccion, uom_unidad, 6200.00),
        ('HIERRO-003', '7890002000014', 'Hierro 10mm Barra 12m', cat_construccion, uom_unidad, 9500.00),
        ('HIERRO-004', '7890002000015', 'Hierro 12mm Barra 12m', cat_construccion, uom_unidad, 13500.00),
        ('ALAMBRE-001', '7890002000016', 'Alambre Negro kg', cat_construccion, uom_kg, 850.00),
        ('ALAMBRE-002', '7890002000017', 'Alambre Recocido kg', cat_construccion, uom_kg, 920.00),
        ('TORN-001', '7890002000018', 'Tornillo Autoperforante 8x1" x100', cat_construccion, uom_paquete, 1250.00),
        ('TORN-002', '7890002000019', 'Tornillo Autoperforante 8x2" x100', cat_construccion, uom_paquete, 1650.00),
        ('CLAV-001', '7890002000020', 'Clavo 2" kg', cat_construccion, uom_kg, 1150.00),
        ('CLAV-002', '7890002000021', 'Clavo 3" kg', cat_construccion, uom_kg, 1250.00),
        ('CLAV-003', '7890002000022', 'Clavo 4" kg', cat_construccion, uom_kg, 1350.00),
        ('GRAMP-001', '7890002000023', 'Grampa Carpintero 10mm x100', cat_construccion, uom_paquete, 850.00),
        ('TACO-001', '7890002000024', 'Taco Fischer 8mm x100', cat_construccion, uom_paquete, 1450.00),
        ('TACO-002', '7890002000025', 'Taco Fischer 10mm x100', cat_construccion, uom_paquete, 1850.00),
        
        # ELECTRICIDAD (20 productos)
        ('CABLE-001', '7890003000001', 'Cable 1.5mm Rollo 100m', cat_electricidad, uom_metro, 45.00),
        ('CABLE-002', '7890003000002', 'Cable 2.5mm Rollo 100m', cat_electricidad, uom_metro, 78.00),
        ('CABLE-003', '7890003000003', 'Cable 4mm Rollo 100m', cat_electricidad, uom_metro, 125.00),
        ('CABLE-004', '7890003000004', 'Cable 6mm Rollo 100m', cat_electricidad, uom_metro, 185.00),
        ('TOMA-001', '7890003000005', 'Tomacorriente 10A', cat_electricidad, uom_unidad, 650.00),
        ('TOMA-002', '7890003000006', 'Tomacorriente 20A', cat_electricidad, uom_unidad, 950.00),
        ('INTER-001', '7890003000007', 'Interruptor Simple', cat_electricidad, uom_unidad, 550.00),
        ('INTER-002', '7890003000008', 'Interruptor Doble', cat_electricidad, uom_unidad, 850.00),
        ('INTER-003', '7890003000009', 'Interruptor Conmutador', cat_electricidad, uom_unidad, 1150.00),
        ('TERMICA-001', '7890003000010', 'Térmica Unipolar 10A', cat_electricidad, uom_unidad, 1850.00),
        ('TERMICA-002', '7890003000011', 'Térmica Unipolar 16A', cat_electricidad, uom_unidad, 1950.00),
        ('TERMICA-003', '7890003000012', 'Térmica Bipolar 25A', cat_electricidad, uom_unidad, 3250.00),
        ('DISYUN-001', '7890003000013', 'Disyuntor Diferencial 25A', cat_electricidad, uom_unidad, 8500.00),
        ('DISYUN-002', '7890003000014', 'Disyuntor Diferencial 40A', cat_electricidad, uom_unidad, 9850.00),
        ('LAMP-001', '7890003000015', 'Lámpara LED 9W E27', cat_electricidad, uom_unidad, 850.00),
        ('LAMP-002', '7890003000016', 'Lámpara LED 12W E27', cat_electricidad, uom_unidad, 1050.00),
        ('LAMP-003', '7890003000017', 'Tubo LED 18W 120cm', cat_electricidad, uom_unidad, 2450.00),
        ('CAÑO-001', '7890003000018', 'Caño Corrugado 3/4" x50m', cat_electricidad, uom_metro, 65.00),
        ('CAÑO-002', '7890003000019', 'Caño Corrugado 1" x50m', cat_electricidad, uom_metro, 85.00),
        ('CINTA-AISL', '7890003000020', 'Cinta Aisladora', cat_electricidad, uom_unidad, 350.00),
        
        # PINTURA (15 productos)
        ('PINT-001', '7890004000001', 'Látex Interior Blanco 20L', cat_pintura, uom_litro, 1250.00),
        ('PINT-002', '7890004000002', 'Látex Interior Color 20L', cat_pintura, uom_litro, 1450.00),
        ('PINT-003', '7890004000003', 'Látex Exterior Blanco 20L', cat_pintura, uom_litro, 1650.00),
        ('PINT-004', '7890004000004', 'Látex Exterior Color 20L', cat_pintura, uom_litro, 1850.00),
        ('SINT-001', '7890004000005', 'Esmalte Sintético Blanco 1L', cat_pintura, uom_litro, 2850.00),
        ('SINT-002', '7890004000006', 'Esmalte Sintético Color 1L', cat_pintura, uom_litro, 3250.00),
        ('SINT-003', '7890004000007', 'Esmalte Sintético Negro 1L', cat_pintura, uom_litro, 3450.00),
        ('BARN-001', '7890004000008', 'Barniz Marino 1L', cat_pintura, uom_litro, 4850.00),
        ('BARN-002', '7890004000009', 'Barniz Sintético 1L', cat_pintura, uom_litro, 3650.00),
        ('AGUAR-001', '7890004000010', 'Aguarrás 1L', cat_pintura, uom_litro, 1150.00),
        ('DILUY-001', '7890004000011', 'Diluyente 1L', cat_pintura, uom_litro, 1250.00),
        ('ENDUIDO-001', '7890004000012', 'Enduido Exterior 20kg', cat_pintura, uom_kg, 3850.00),
        ('ENDUIDO-002', '7890004000013', 'Enduido Interior 20kg', cat_pintura, uom_kg, 3250.00),
        ('RODILLO-001', '7890004000014', 'Rodillo Pelo Corto 23cm', cat_pintura, uom_unidad, 1450.00),
        ('PINCEL-001', '7890004000015', 'Pincel 2" Cerda', cat_pintura, uom_unidad, 850.00),
        
        # PLOMERÍA (15 productos)
        ('CAÑO-PVC-001', '7890005000001', 'Caño PVC 1/2" x3m', cat_plomeria, uom_unidad, 850.00),
        ('CAÑO-PVC-002', '7890005000002', 'Caño PVC 3/4" x3m', cat_plomeria, uom_unidad, 1150.00),
        ('CAÑO-PVC-003', '7890005000003', 'Caño PVC 1" x3m', cat_plomeria, uom_unidad, 1650.00),
        ('CAÑO-PVC-004', '7890005000004', 'Caño PVC 1½" x3m', cat_plomeria, uom_unidad, 2450.00),
        ('CAÑO-PVC-005', '7890005000005', 'Caño PVC 2" x3m', cat_plomeria, uom_unidad, 3250.00),
        ('CODO-001', '7890005000006', 'Codo PVC 1/2" 90°', cat_plomeria, uom_unidad, 180.00),
        ('CODO-002', '7890005000007', 'Codo PVC 3/4" 90°', cat_plomeria, uom_unidad, 220.00),
        ('CODO-003', '7890005000008', 'Codo PVC 1" 90°', cat_plomeria, uom_unidad, 320.00),
        ('TEE-001', '7890005000009', 'Tee PVC 1/2"', cat_plomeria, uom_unidad, 250.00),
        ('TEE-002', '7890005000010', 'Tee PVC 3/4"', cat_plomeria, uom_unidad, 350.00),
        ('CANILLA-001', '7890005000011', 'Canilla Jardín 1/2"', cat_plomeria, uom_unidad, 1850.00),
        ('CANILLA-002', '7890005000012', 'Canilla Cocina Monocomando', cat_plomeria, uom_unidad, 8500.00),
        ('CANILLA-003', '7890005000013', 'Grifería Baño Simple', cat_plomeria, uom_unidad, 6850.00),
        ('TEFLON-001', '7890005000014', 'Cinta Teflón', cat_plomeria, uom_unidad, 250.00),
        ('PEGAMENTO-001', '7890005000015', 'Pegamento PVC 250ml', cat_plomeria, uom_unidad, 1450.00),
    ]
    
    products = []
    for sku, barcode, name, category, uom, price in products_data:
        product = Product(
            sku=sku,
            barcode=barcode,
            name=name,
            category=category,
            uom=uom,
            sale_price=Decimal(str(price)),
            active=True
        )
        session.add(product)
        products.append(product)
    
    session.commit()
    print(f"✅ Inserted {len(products)} products")
    return products


def seed_purchase_invoices(session, suppliers, products):
    """Create sample purchase invoices."""
    print("\n" + "="*60)
    print("INSERTING PURCHASE INVOICES")
    print("="*60)
    
    # Create 10 invoices over the last 60 days
    invoices_created = 0
    
    for i in range(10):
        # Random supplier
        supplier = random.choice(suppliers)
        
        # Random date in last 60 days
        days_ago = random.randint(1, 60)
        invoice_date = date.today() - timedelta(days=days_ago)
        
        # Random due date (30-60 days after invoice)
        due_date = invoice_date + timedelta(days=random.randint(30, 60))
        
        # Random invoice number
        invoice_number = f"FC-{invoice_date.strftime('%Y%m')}-{random.randint(1000, 9999)}"
        
        # Select 5-15 random products for this invoice
        num_products = random.randint(5, 15)
        selected_products = random.sample(products, num_products)
        
        # Calculate total
        total_amount = Decimal('0.00')
        lines_data = []
        
        for product in selected_products:
            qty = Decimal(str(random.randint(10, 100)))
            # Cost is 60-80% of sale price
            unit_cost = product.sale_price * Decimal(str(random.uniform(0.60, 0.80)))
            unit_cost = unit_cost.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            line_total = round_decimal(qty * unit_cost, 2)
            total_amount += line_total
            
            lines_data.append({
                'product': product,
                'qty': qty,
                'unit_cost': unit_cost,
                'line_total': line_total
            })
        
        # Decide if paid or pending (70% paid)
        is_paid = random.random() < 0.7
        status = 'PAID' if is_paid else 'PENDING'
        paid_at = invoice_date + timedelta(days=random.randint(1, 20)) if is_paid else None
        
        # Begin transaction
        with session.begin_nested():
            # Create invoice
            invoice = PurchaseInvoice(
                supplier=supplier,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                total_amount=total_amount,
                status=status,
                paid_at=paid_at
            )
            session.add(invoice)
            session.flush()
            
            # Create invoice lines
            for line_data in lines_data:
                line = PurchaseInvoiceLine(
                    invoice=invoice,
                    product=line_data['product'],
                    qty=line_data['qty'],
                    unit_cost=line_data['unit_cost'],
                    line_total=line_data['line_total']
                )
                session.add(line)
            
            # Create stock movement (IN)
            stock_move = StockMove(
                date=invoice_date,
                type='IN',
                reference_type='INVOICE',
                reference_id=invoice.id,
                notes=f'Compra - Factura {invoice_number} - {supplier.name}'
            )
            session.add(stock_move)
            session.flush()
            
            # Create stock move lines
            for line_data in lines_data:
                stock_line = StockMoveLine(
                    stock_move=stock_move,
                    product=line_data['product'],
                    qty=line_data['qty'],
                    uom=line_data['product'].uom,
                    unit_cost=line_data['unit_cost']
                )
                session.add(stock_line)
            
            # If paid, create ledger entry (EXPENSE)
            if is_paid:
                ledger_entry = FinanceLedger(
                    datetime=datetime.combine(paid_at, datetime.min.time()),
                    type='EXPENSE',
                    amount=total_amount,
                    category='Compras',
                    reference_type='INVOICE_PAYMENT',
                    reference_id=invoice.id,
                    notes=f'Pago Factura {invoice_number} - {supplier.name}'
                )
                session.add(ledger_entry)
        
        session.commit()
        invoices_created += 1
        print(f"  ✓ Invoice {invoice_number} - ${total_amount:.2f} - {status}")
    
    print(f"✅ Created {invoices_created} purchase invoices with stock movements")


def seed_sales(session, products):
    """Create sample sales."""
    print("\n" + "="*60)
    print("INSERTING SALES")
    print("="*60)
    
    # Get products with stock > 0
    products_with_stock = []
    for product in products:
        stock = session.query(ProductStock).filter_by(product_id=product.id).first()
        if stock and stock.on_hand_qty > 0:
            products_with_stock.append(product)
    
    print(f"  Found {len(products_with_stock)} products with stock available")
    
    # Create 15 sales over the last 30 days
    sales_created = 0
    
    for i in range(15):
        # Random date in last 30 days
        days_ago = random.randint(1, 30)
        sale_date = datetime.now() - timedelta(days=days_ago)
        
        # Select 1-5 random products with stock
        num_products = min(random.randint(1, 5), len(products_with_stock))
        if num_products == 0:
            continue
            
        selected_products = random.sample(products_with_stock, num_products)
        
        # Calculate total
        total = Decimal('0.00')
        lines_data = []
        
        for product in selected_products:
            stock = session.query(ProductStock).filter_by(product_id=product.id).first()
            
            # Random qty (but not more than available stock and max 10)
            max_qty = min(int(stock.on_hand_qty), 10)
            if max_qty < 1:
                continue
            
            qty = Decimal(str(random.randint(1, max_qty)))
            unit_price = product.sale_price
            line_total = round_decimal(qty * unit_price, 2)
            total += line_total
            
            lines_data.append({
                'product': product,
                'qty': qty,
                'unit_price': unit_price,
                'line_total': line_total
            })
        
        if not lines_data:
            continue
        
        # Begin transaction
        with session.begin_nested():
            # Create sale
            sale = Sale(
                datetime=sale_date,
                total=total,
                status='CONFIRMED'
            )
            session.add(sale)
            session.flush()
            
            # Create sale lines
            for line_data in lines_data:
                line = SaleLine(
                    sale=sale,
                    product=line_data['product'],
                    qty=line_data['qty'],
                    unit_price=line_data['unit_price'],
                    line_total=line_data['line_total']
                )
                session.add(line)
            
            # Create stock movement (OUT)
            stock_move = StockMove(
                date=sale_date,
                type='OUT',
                reference_type='SALE',
                reference_id=sale.id,
                notes=f'Venta #{sale.id}'
            )
            session.add(stock_move)
            session.flush()
            
            # Create stock move lines
            for line_data in lines_data:
                stock_line = StockMoveLine(
                    stock_move=stock_move,
                    product=line_data['product'],
                    qty=line_data['qty'],
                    uom=line_data['product'].uom,
                    unit_cost=Decimal('0.00')  # For sales, cost is not tracked in move
                )
                session.add(stock_line)
            
            # Create ledger entry (INCOME)
            ledger_entry = FinanceLedger(
                datetime=sale_date,
                type='INCOME',
                amount=total,
                category='Ventas',
                reference_type='SALE',
                reference_id=sale.id,
                notes=f'Venta #{sale.id}'
            )
            session.add(ledger_entry)
        
        session.commit()
        sales_created += 1
        print(f"  ✓ Sale #{sale.id} - ${total:.2f}")
    
    print(f"✅ Created {sales_created} sales with stock movements and ledger entries")


def main():
    """Main seed function."""
    print("\n" + "="*60)
    print("SEED SAMPLE DATA - FERRETERÍA")
    print("="*60)
    print("This script will populate the database with sample data:")
    print("  • 5 suppliers")
    print("  • ~100 products")
    print("  • 10 purchase invoices (with stock IN)")
    print("  • 15 sales (with stock OUT)")
    print("  • Finance ledger entries")
    print("="*60)
    
    app = create_app()
    
    with app.app_context():
        session = get_session()
        
        try:
            # Check if already has data
            existing_products = session.query(Product).count()
            if existing_products > 0:
                print(f"\n⚠️  WARNING: Database already has {existing_products} products.")
                print("   This script will ADD MORE data (not replace).")
                response = input("   Continue? (yes/no): ").lower()
                if response != 'yes':
                    print("Cancelled.")
                    return
            
            # Seed suppliers
            suppliers = seed_suppliers(session)
            
            # Seed products
            products = seed_products(session)
            
            # Seed purchase invoices (this creates stock)
            seed_purchase_invoices(session, suppliers, products)
            
            # Seed sales (this reduces stock)
            seed_sales(session, products)
            
            print("\n" + "="*60)
            print("✅ SEED COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nSummary:")
            print(f"  • Suppliers: {len(suppliers)}")
            print(f"  • Products: {len(products)}")
            print(f"  • Purchase Invoices: Check output above")
            print(f"  • Sales: Check output above")
            print("\nYou can now:")
            print("  • Browse products at: http://localhost:5000/products")
            print("  • View invoices at: http://localhost:5000/invoices")
            print("  • Check balance at: http://localhost:5000/balance")
            print("="*60)
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            session.close()


if __name__ == '__main__':
    # Reconfigure stdout for UTF-8 (Windows compatibility)
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    main()
