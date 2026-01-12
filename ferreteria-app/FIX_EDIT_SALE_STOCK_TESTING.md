# FIX: Stock Adjustment on Sale Edit - Testing Guide

## Bug Description
**Critical:** When editing a confirmed sale, stock was NOT updating correctly.

**Root Cause:** 
1. Trigger for `ADJUST` type was always adding qty (no support for negative)
2. Code was doing DOUBLE update: trigger + manual update
3. `stock_move_line.qty` had CHECK constraint preventing negative values

## Fix Applied
1. **Trigger updated:** ADJUST now interprets qty as signed (negative = reduce, positive = increase)
2. **Code cleaned:** Removed manual stock update, now relies solely on trigger
3. **Constraint updated:** `stock_move_line.qty` now allows negative values for ADJUST
4. **DDL updated:** Schema reflects new constraint

---

## Test Cases (MANDATORY)

### Pre-requisites
- Have at least one confirmed sale with multiple lines
- Know the product IDs and their current stock levels
- Access to database for verification queries

---

### Test 1: Increase Quantity (+2 units)
**Scenario:** User sold 5, corrects to 7 (delta = +2)

**Steps:**
1. Note initial stock for product:
   ```sql
   SELECT p.id, p.name, ps.on_hand_qty
   FROM product p
   JOIN product_stock ps ON ps.product_id = p.id
   WHERE p.id = <product_id>;
   ```
   Example: Initial stock = 10

2. Edit sale, change qty from 5 to 7

3. Verify stock decreased by 2:
   ```sql
   SELECT ps.on_hand_qty FROM product_stock ps WHERE ps.product_id = <product_id>;
   ```
   **Expected:** Stock = 8 (10 - 2)

4. Verify ADJUST stock_move created:
   ```sql
   SELECT sm.id, sm.type, sm.reference_type, sm.reference_id, sm.notes
   FROM stock_move sm
   WHERE sm.reference_id = <sale_id> AND sm.type = 'ADJUST'
   ORDER BY sm.id DESC
   LIMIT 1;
   ```
   **Expected:** 1 row with type='ADJUST', reference_id=sale_id

5. Verify stock_move_line with NEGATIVE qty:
   ```sql
   SELECT sml.product_id, sml.qty
   FROM stock_move_line sml
   WHERE sml.stock_move_id = <adjust_move_id> AND sml.product_id = <product_id>;
   ```
   **Expected:** qty = -2 (negative because we sold MORE)

---

### Test 2: Decrease Quantity (-3 units)
**Scenario:** User sold 10, corrects to 7 (delta = -3)

**Steps:**
1. Note initial stock (e.g., 5)
2. Edit sale, change qty from 10 to 7
3. Verify stock **increased** by 3
   **Expected:** Stock = 8 (5 + 3)
4. Verify ADJUST with POSITIVE qty = +3

---

### Test 3: Remove Product Line
**Scenario:** User removes entire product from sale (was 4 units)

**Steps:**
1. Note initial stock (e.g., 12)
2. Edit sale, delete the product line
3. Verify stock **increased** by 4
   **Expected:** Stock = 16 (12 + 4)
4. Verify ADJUST with POSITIVE qty = +4

---

### Test 4: Add New Product
**Scenario:** User adds a new product (3 units) not in original sale

**Steps:**
1. Note initial stock (e.g., 20)
2. Edit sale, add new product with qty = 3
3. Verify stock **decreased** by 3
   **Expected:** Stock = 17 (20 - 3)
4. Verify ADJUST with NEGATIVE qty = -3

---

### Test 5: Insufficient Stock (Should Fail)
**Scenario:** User tries to increase qty but stock is insufficient

**Steps:**
1. Product with stock = 2
2. Try to increase sale qty by +5 (delta = +5)
3. **Expected:** Transaction fails with error message
4. Verify:
   - Sale unchanged
   - Stock unchanged (still 2)
   - No new stock_move created
   - No new stock_move_line created

---

### Test 6: Multiple Changes in One Edit
**Scenario:** Complex edit with multiple deltas

**Steps:**
1. Product A: increase qty +2 (stock should decrease 2)
2. Product B: decrease qty -1 (stock should increase 1)
3. Product C: remove (stock should increase by original qty)
4. Product D: add 3 units (stock should decrease 3)

5. Verify:
   - All stock changes correct
   - One ADJUST stock_move created
   - Four stock_move_line entries with correct signs

---

## Verification Queries

### Check Latest Stock Moves
```sql
SELECT sm.id, sm.type, sm.reference_type, sm.reference_id, sm.date, sm.notes
FROM stock_move sm
ORDER BY sm.id DESC
LIMIT 10;
```

### Check Latest Stock Move Lines
```sql
SELECT sml.id, sml.stock_move_id, sml.product_id, p.name, sml.qty
FROM stock_move_line sml
JOIN product p ON p.id = sml.product_id
ORDER BY sml.id DESC
LIMIT 20;
```

### Check Stock for Specific Product
```sql
SELECT p.id, p.name, ps.on_hand_qty
FROM product p
LEFT JOIN product_stock ps ON ps.product_id = p.id
WHERE p.id = <product_id>;
```

### Check All Moves for a Sale
```sql
SELECT sm.id, sm.type, sm.date, sml.product_id, p.name, sml.qty
FROM stock_move sm
JOIN stock_move_line sml ON sml.stock_move_id = sm.id
JOIN product p ON p.id = sml.product_id
WHERE sm.reference_id = <sale_id>
ORDER BY sm.id;
```

---

## Success Criteria

✅ All test cases pass
✅ Stock updates correctly (increases/decreases match deltas)
✅ ADJUST stock_move created with correct reference
✅ stock_move_line entries have correct signed qty
✅ Insufficient stock is properly blocked with rollback
✅ No manual stock updates (all via trigger)
✅ Existing sales/purchases/invoices unaffected

---

## Files Modified

1. **db/init/001_schema.sql**
   - Updated trigger `trg_stock_move_line_after_ins()` to support signed qty for ADJUST
   - Updated `stock_move_line.qty` constraint to allow negative values

2. **db/migrations/FIX_stock_adjust_trigger.sql**
   - Migration to update trigger in existing database

3. **db/migrations/FIX_allow_negative_qty_for_adjust.sql**
   - Migration to remove qty > 0 constraint and add qty != 0 constraint

4. **app/services/sale_adjustment_service.py**
   - Removed manual `product_stock` update (lines 216-227 deleted)
   - Simplified stock_move_line creation to use signed qty
   - Now relies 100% on trigger for stock updates

---

## Rollback (if needed)

If issues occur, rollback with:

```sql
BEGIN;

-- Restore old trigger
CREATE OR REPLACE FUNCTION trg_stock_move_line_after_ins()
RETURNS TRIGGER AS $$
DECLARE
  v_type stock_move_type;
  v_delta NUMERIC(12,3);
BEGIN
  SELECT type INTO v_type FROM stock_move WHERE id = NEW.stock_move_id;
  IF v_type = 'IN' THEN
    v_delta := NEW.qty;
  ELSIF v_type = 'OUT' THEN
    v_delta := -NEW.qty;
  ELSE
    v_delta := NEW.qty;  -- Old behavior: always positive
  END IF;
  PERFORM apply_stock_delta(NEW.product_id, v_delta);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Restore old constraint
ALTER TABLE stock_move_line DROP CONSTRAINT IF EXISTS stock_move_line_qty_nonzero_check;
ALTER TABLE stock_move_line ADD CONSTRAINT stock_move_line_qty_check CHECK (qty > 0);

COMMIT;
```

Then restore old code from git.
