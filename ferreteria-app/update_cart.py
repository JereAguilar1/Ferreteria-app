import re

with open('app/templates/sales/_cart.html', 'r') as f:
    content = f.read()

# Replace the single TOTAL row with Subtotal, Flete, and Total
old_tfoot = """            <tfoot>
                <tr class="table-active">
                    <td colspan="4" class="text-end"><strong>TOTAL:</strong></td>
                    <td class="text-end">
                        <h5 class="mb-0">${{ cart_total|money_ar }}</h5>
                    </td>
                    <td></td>
                </tr>
            </tfoot>"""

new_tfoot = """            <tfoot>
                <tr>
                    <td colspan="4" class="text-end"><strong>Subtotal:</strong></td>
                    <td class="text-end">
                        <h5 class="mb-0" id="cart_subtotal" data-subtotal="{{ cart_total }}">${{ cart_total|money_ar }}</h5>
                    </td>
                    <td></td>
                </tr>
                <tr>
                    <td colspan="4" class="text-end"><strong>Flete:</strong></td>
                    <td class="text-end">
                        <h5 class="mb-0 text-muted" id="cart_shipping_display">$0.00</h5>
                    </td>
                    <td></td>
                </tr>
                <tr class="table-active">
                    <td colspan="4" class="text-end"><strong>TOTAL:</strong></td>
                    <td class="text-end">
                        <h5 class="mb-0 text-primary" id="cart_grand_total">${{ cart_total|money_ar }}</h5>
                    </td>
                    <td></td>
                </tr>
            </tfoot>"""

content = content.replace(old_tfoot, new_tfoot)

# Add Shipping Cost Input before Payment Method
old_payment_header = """    <!-- MEJORA 12/15: Payment Method Selection + Confirm Button -->
    <div class="card mb-3">
        <div class="card-body">
            <h6 class="card-title mb-3">
                <i class="bi bi-cash-coin"></i> Método de Pago
            </h6>"""

new_payment_header = """    <!-- Shipping Cost and Payment Method -->
    <div class="card mb-3">
        <div class="card-body">
            
            <h6 class="card-title mb-3">
                <i class="bi bi-truck"></i> Costo de Flete
            </h6>
            <div class="input-group mb-4">
                <span class="input-group-text">$</span>
                <input type="number" id="shipping_cost_input" class="form-control" value="0" min="0" step="0.01" placeholder="Ej: 50.00">
            </div>
            
            <h6 class="card-title mb-3">
                <i class="bi bi-cash-coin"></i> Método de Pago
            </h6>"""

content = content.replace(old_payment_header, new_payment_header)

# Update the Confirm Button's hx-vals
old_button = """                <button type="button" 
                        class="btn btn-success btn-lg"
                        hx-get="{{ url_for('sales.confirm_preview') }}"
                        hx-target="#modal-container"
                        hx-swap="innerHTML"
                        hx-vals='js:{"payment_method": document.querySelector("input[name=payment_method]:checked").value}'
                        hx-indicator="#loading-indicator">
                    <i class="bi bi-check-circle"></i> Confirmar Venta (${{ cart_total|money_ar }})
                </button>"""

new_button = """                <button type="button" 
                        class="btn btn-success btn-lg"
                        id="btn_confirm_preview"
                        hx-get="{{ url_for('sales.confirm_preview') }}"
                        hx-target="#modal-container"
                        hx-swap="innerHTML"
                        hx-vals='js:{"payment_method": document.querySelector("input[name=payment_method]:checked").value, "shipping_cost": document.getElementById("shipping_cost_input").value || "0"}'
                        hx-indicator="#loading-indicator">
                    <i class="bi bi-check-circle"></i> Confirmar Venta (<span id="btn_grand_total">${{ cart_total|money_ar }}</span>)
                </button>
                
                <script>
                    document.getElementById('shipping_cost_input').addEventListener('input', function() {
                        let shipping = parseFloat(this.value) || 0;
                        let subtotal = parseFloat(document.getElementById('cart_subtotal').dataset.subtotal) || 0;
                        let total = subtotal + shipping;
                        
                        // Simple formatting for frontend preview, backend does the real validation
                        let fmtShipping = '$' + shipping.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        let fmtTotal = '$' + total.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        
                        document.getElementById('cart_shipping_display').textContent = fmtShipping;
                        document.getElementById('cart_grand_total').textContent = fmtTotal;
                        document.getElementById('btn_grand_total').textContent = fmtTotal;
                    });
                </script>"""

content = content.replace(old_button, new_button)

with open('app/templates/sales/_cart.html', 'w') as f:
    f.write(content)

print("Template updated successfully")
