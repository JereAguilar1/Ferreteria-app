# Specification: Duplicate Invoice (Boleta) Feature

## Overview
The goal of this track is to facilitate the creation of new invoices by allowing users to copy an existing "boleta". This is especially useful when a customer requests an invoice similar to a previous one, requiring only minor modifications to the products or quantities, saving time on data entry.

## Functional Requirements
1. **Trigger Action:** The boletas list view must include a "Duplicate" button or icon next to each existing boleta.
2. **Data Copying & Reset:**
   - When triggered, the system must copy the customer data and the list of products (including prices/quantities) from the selected boleta.
   - The system MUST reset the invoice date to the current date.
   - The system MUST clear or generate a new unique invoice number (depending on the system's generation logic).
3. **Workflow Integration:**
   - After clicking "Duplicate", the user should be immediately redirected to the "Create/Edit Boleta" form.
   - The form must be pre-filled with the copied data.
   - The boleta must NOT be saved automatically; it requires the user to explicitly click "Save" after making any desired modifications.

## Non-Functional Requirements
- **Performance:** Copying and redirecting should happen instantly without noticeable lag.
- **UX:** The "Duplicate" action should be easily recognizable (e.g., a copy icon) and positioned intuitively in the list.

## Acceptance Criteria
- [ ] A user can see a "Duplicate" option on the boletas list.
- [ ] Clicking "Duplicate" opens the creation form.
- [ ] The form contains the products and customer from the original boleta.
- [ ] The date is set to today and the invoice number is new/empty.
- [ ] The user can add/remove products and modify quantities before saving.
- [ ] Saving creates a completely independent boleta without altering the original.

## Out of Scope
- Bulk duplication of multiple boletas at once.
- Copying boletas from different business branches or unsupported older formats.
