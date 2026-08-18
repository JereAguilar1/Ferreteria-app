# Implementation Plan: Agregar Costo de Flete a Boleta

## Phase 1: Database & Model Update [checkpoint: 2be2c10]
- [x] Task: Write failing tests for Database/Model (Red Phase) 2be2c10
  - [x] Write unit tests asserting that the Sale/Boleta model correctly handles the `shipping_cost` attribute (default value 0).
- [x] Task: Implement Database changes (Green Phase) 2be2c10
  - [x] Add `shipping_cost` column (Numeric/Float) to the SQLAlchemy model.
  - [x] Generate Alembic migration for the new column.
  - [x] Apply Alembic migration to the local database.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 2be2c10

## Phase 2: Backend Logic (Total Calculation & Endpoints) [checkpoint: 5461872]
- [x] Task: Write failing tests for Backend Logic (Red Phase) 5461872
  - [x] Write tests to verify that creating a sale correctly calculates `Total = Subtotal + Flete`.
  - [x] Write tests to ensure the endpoint correctly processes `shipping_cost` from incoming form data/JSON.
- [x] Task: Implement Backend Logic (Green Phase) 5461872
  - [x] Update the backend service or logic layer to include `shipping_cost` in the total calculation.
  - [x] Update the corresponding Flask routes/views to accept and process the `shipping_cost` parameter.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 5461872

## Phase 3: Frontend UI Updates (HTMX) [checkpoint: 387c16e]
- [x] Task: Write failing tests for UI/Frontend interactions (Red Phase) 387c16e
  - [x] Write/update tests (if automated tests for templates exist) to verify the new fields are rendered correctly.
- [x] Task: Implement UI changes (Green Phase) 387c16e
  - [x] Update the Boleta creation form (Jinja2 template) to include the `Costo de Flete` numeric input, opcional y con valor por defecto 0.
  - [x] Update the summary section in the template to display "Subtotal", "Flete", y "Total".
  - [x] Add HTMX bindings if necessary to recalculate and update the live "Total" when the "Flete" input changes.
  - [x] Update the sale detail/receipt view template to show the new breakdown.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) 387c16e
