# Implementation Plan: Mover Costo de Flete de Ventas a Compras

## Phase 1: Revert Sales Freight Feature
- [x] Task: Revert failing tests for Backend Logic (Red Phase) 0f64fac
  - [x] Modify `test_flete_boleta.py` (or completely remove it) to expect `Sale` without `shipping_cost`.
- [x] Task: Revert Database changes (Green Phase) 5a6956f
  - [x] Remove `shipping_cost` from `app/models/sale.py`.
  - [x] Revert `chk_sale_total_matches_lines` trigger logic and remove `shipping_cost` from `sale` table in `db/init/001_schema.sql`.
  - [x] Apply the schema reversion manually via SQL `ALTER TABLE` and `CREATE OR REPLACE FUNCTION` in the running local database.
- [ ] Task: Revert Backend Logic (Green Phase)
  - [ ] Revert changes in `app/services/sales_service.py` to remove `shipping_cost` from total calculation.
  - [ ] Revert changes in `app/blueprints/sales.py` to stop accepting `shipping_cost`.
- [ ] Task: Revert Frontend UI Updates (Green Phase)
  - [ ] Remove `shipping_cost` inputs and fields from `app/templates/sales/_cart.html`, `app/templates/sales/_confirm_modal.html`, and `app/templates/sales/detail.html`.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: Purchase Freight Database & Models
- [ ] Task: Write failing tests for Database/Model (Red Phase)
  - [ ] Create tests to verify that `PurchaseInvoice` correctly handles the `shipping_cost` attribute (default 0).
- [ ] Task: Implement Database changes (Green Phase)
  - [ ] Add `shipping_cost` (Numeric) to `app/models/purchase_invoice.py`.
  - [ ] Update `db/init/001_schema.sql` to add `shipping_cost` to the `purchase_invoice` table and update the `chk_invoice_total_matches_lines` trigger.
  - [ ] Apply changes directly to the running PostgreSQL container.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Purchase Freight Backend Logic
- [ ] Task: Write failing tests for Backend Logic (Red Phase)
  - [ ] Write unit tests to assert that `Total = Subtotal + Flete` when saving a new purchase invoice.
- [ ] Task: Implement Backend Logic (Green Phase)
  - [ ] Update the purchase creation logic (e.g., in `purchase_service.py` or controllers) to include `shipping_cost`.
  - [ ] Update the route handling invoice submission to accept the parameter from the frontend.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: Purchase Freight Frontend UI
- [ ] Task: Write failing tests for UI/Frontend interactions (Red Phase)
  - [ ] Write or specify manual test scripts for rendering the purchase UI correctly with the new field.
- [ ] Task: Implement UI changes (Green Phase)
  - [ ] Update the purchase invoice creation form (`app/templates/purchases/...`) to include an optional `Costo de Flete` input.
  - [ ] Update the summary/totals sections to show "Subtotal", "Flete" y "Total".
  - [ ] Update the purchase detail view to show the breakdown of costs.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
