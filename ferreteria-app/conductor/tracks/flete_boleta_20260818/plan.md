# Implementation Plan: Agregar Costo de Flete a Boleta

## Phase 1: Database & Model Update
- [ ] Task: Write failing tests for Database/Model (Red Phase)
  - [ ] Write unit tests asserting that the Sale/Boleta model correctly handles the `shipping_cost` attribute (default value 0).
- [ ] Task: Implement Database changes (Green Phase)
  - [ ] Add `shipping_cost` column (Numeric/Float) to the SQLAlchemy model.
  - [ ] Generate Alembic migration for the new column.
  - [ ] Apply Alembic migration to the local database.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: Backend Logic (Total Calculation & Endpoints)
- [ ] Task: Write failing tests for Backend Logic (Red Phase)
  - [ ] Write tests to verify that creating a sale correctly calculates `Total = Subtotal + Flete`.
  - [ ] Write tests to ensure the endpoint correctly processes `shipping_cost` from incoming form data/JSON.
- [ ] Task: Implement Backend Logic (Green Phase)
  - [ ] Update the backend service or logic layer to include `shipping_cost` in the total calculation.
  - [ ] Update the corresponding Flask routes/views to accept and process the `shipping_cost` parameter.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Frontend UI Updates (HTMX)
- [ ] Task: Write failing tests for UI/Frontend interactions (Red Phase)
  - [ ] Write/update tests (if automated tests for templates exist) to verify the new fields are rendered correctly.
- [ ] Task: Implement UI changes (Green Phase)
  - [ ] Update the Boleta creation form (Jinja2 template) to include the `Costo de Flete` numeric input, opcional y con valor por defecto 0.
  - [ ] Update the summary section in the template to display "Subtotal", "Flete", y "Total".
  - [ ] Add HTMX bindings if necessary to recalculate and update the live "Total" when the "Flete" input changes.
  - [ ] Update the sale detail/receipt view template to show the new breakdown.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
