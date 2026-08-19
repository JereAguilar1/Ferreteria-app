import re

with open('app/templates/sales/detail.html', 'r') as f:
    content = f.read()

old_tfoot = """                <tfoot class="table-light">
                    <tr>
                        <td colspan="3" class="text-end"><strong>TOTAL:</strong></td>
                        <td class="text-end">
                            <h5 class="mb-0 text-success">
                                <strong>${{ "%.2f"|format(sale.total) }}</strong>
                            </h5>
                        </td>
                    </tr>
                </tfoot>"""

new_tfoot = """                <tfoot class="table-light">
                    <tr>
                        <td colspan="3" class="text-end"><strong>Subtotal:</strong></td>
                        <td class="text-end"><strong>${{ "%.2f"|format(sale.total - sale.shipping_cost) }}</strong></td>
                    </tr>
                    <tr>
                        <td colspan="3" class="text-end"><strong>Flete:</strong></td>
                        <td class="text-end"><strong>${{ "%.2f"|format(sale.shipping_cost) }}</strong></td>
                    </tr>
                    <tr>
                        <td colspan="3" class="text-end"><strong>TOTAL:</strong></td>
                        <td class="text-end">
                            <h5 class="mb-0 text-success">
                                <strong>${{ "%.2f"|format(sale.total) }}</strong>
                            </h5>
                        </td>
                    </tr>
                </tfoot>"""

content = content.replace(old_tfoot, new_tfoot)

with open('app/templates/sales/detail.html', 'w') as f:
    f.write(content)

print("Detail template updated successfully")
