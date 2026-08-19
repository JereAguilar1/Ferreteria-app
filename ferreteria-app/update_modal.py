import re

with open('app/templates/sales/_confirm_modal.html', 'r') as f:
    content = f.read()

# Update Table Footer
old_tfoot = """                        <tfoot class="table-light">
                            <tr>
                                <td colspan="3" class="text-end"><strong>TOTAL:</strong></td>
                                <td class="text-end">
                                    <h5 class="mb-0 text-primary">
                                        <strong>${{ cart_total|money_ar }}</strong>
                                    </h5>
                                </td>
                            </tr>
                        </tfoot>"""

new_tfoot = """                        <tfoot class="table-light">
                            <tr>
                                <td colspan="3" class="text-end"><strong>Subtotal:</strong></td>
                                <td class="text-end"><strong>${{ cart_total|money_ar }}</strong></td>
                            </tr>
                            <tr>
                                <td colspan="3" class="text-end"><strong>Flete:</strong></td>
                                <td class="text-end"><strong>${{ shipping_cost|money_ar }}</strong></td>
                            </tr>
                            <tr>
                                <td colspan="3" class="text-end"><strong>TOTAL:</strong></td>
                                <td class="text-end">
                                    <h5 class="mb-0 text-primary">
                                        <strong>${{ grand_total|money_ar }}</strong>
                                    </h5>
                                </td>
                            </tr>
                        </tfoot>"""

content = content.replace(old_tfoot, new_tfoot)

# Update Summary list
old_summary = """                        <li>Monto total: <strong>${{ cart_total|money_ar }}</strong></li>"""
new_summary = """                        <li>Monto total: <strong>${{ grand_total|money_ar }}</strong></li>"""
content = content.replace(old_summary, new_summary)

# Update Hidden Inputs in Form
old_form = """                <form method="POST" action="{{ url_for('sales.confirm') }}" id="finalConfirmForm">
                    <input type="hidden" name="payment_method" value="{{ payment_method }}">
                    <button type="submit" class="btn btn-primary">"""

new_form = """                <form method="POST" action="{{ url_for('sales.confirm') }}" id="finalConfirmForm">
                    <input type="hidden" name="payment_method" value="{{ payment_method }}">
                    <input type="hidden" name="shipping_cost" value="{{ shipping_cost }}">
                    <button type="submit" class="btn btn-primary">"""
content = content.replace(old_form, new_form)

with open('app/templates/sales/_confirm_modal.html', 'w') as f:
    f.write(content)

print("Modal template updated successfully")
