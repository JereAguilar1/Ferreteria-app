-- FIX: Add ON DELETE CASCADE to product_stock.product_id FK
-- This allows deleting a product without "blank-out primary key" error
-- When a product is deleted, its product_stock record is automatically deleted

-- Objective:
-- Fix error: "Dependency rule on column 'product.id' tried to blank-out 
-- primary key column 'product_stock.product_id'"

-- Background:
-- product_stock has a 1:1 relationship with product (product_id is both PK and FK)
-- When deleting a product, SQLAlchemy tried to NULL product_stock.product_id,
-- which is impossible because it's a PRIMARY KEY.
-- Solution: Add ON DELETE CASCADE so product_stock is deleted automatically.

BEGIN;

-- Step 1: Check current constraint name
-- Run this query first to verify the constraint name:
-- SELECT constraint_name 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'product_stock' 
--   AND constraint_type = 'FOREIGN KEY';

-- Step 2: Drop existing FK constraint
-- Replace 'product_stock_product_id_fkey' with actual constraint name if different
ALTER TABLE product_stock
DROP CONSTRAINT IF EXISTS product_stock_product_id_fkey;

-- Step 3: Add FK constraint with ON DELETE CASCADE
ALTER TABLE product_stock
ADD CONSTRAINT product_stock_product_id_fkey
FOREIGN KEY (product_id) 
REFERENCES product(id) 
ON DELETE CASCADE;

-- Verification query (run after migration):
-- SELECT 
--   tc.constraint_name,
--   tc.table_name,
--   kcu.column_name,
--   ccu.table_name AS foreign_table_name,
--   ccu.column_name AS foreign_column_name,
--   rc.delete_rule
-- FROM information_schema.table_constraints AS tc
-- JOIN information_schema.key_column_usage AS kcu
--   ON tc.constraint_name = kcu.constraint_name
-- JOIN information_schema.constraint_column_usage AS ccu
--   ON ccu.constraint_name = tc.constraint_name
-- JOIN information_schema.referential_constraints AS rc
--   ON rc.constraint_name = tc.constraint_name
-- WHERE tc.table_name = 'product_stock' 
--   AND tc.constraint_type = 'FOREIGN KEY';
-- Expected: delete_rule = 'CASCADE'

COMMIT;

-- Notes:
-- 1. This is safe because product_stock is a dependent entity (1:1 with product)
-- 2. If a product is deleted, its stock record should also be deleted
-- 3. This does NOT affect other tables (sale_line, purchase_invoice_line, etc.)
--    which still have RESTRICT/NO ACTION to prevent accidental deletion of used products
-- 4. The application logic (can_hard_delete_product) ensures products with references
--    cannot be deleted anyway

-- Testing:
-- After running this migration:
-- 1. Create a test product (it will auto-create product_stock via trigger)
-- 2. Try to delete it: DELETE FROM product WHERE id = <test_id>;
-- 3. Verify product_stock was also deleted: SELECT * FROM product_stock WHERE product_id = <test_id>;
-- 4. Should return 0 rows (product_stock was cascaded)
