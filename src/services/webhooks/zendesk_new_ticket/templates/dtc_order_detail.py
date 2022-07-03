from datetime import datetime
# fedex track url https://www.fedex.com/fedextrack/?trknbr={trackingID}

def make_row(order, items):
    rowspan = len(items) if len(items) > 1 else 1
    html=f"""
            <tr>
                <td class="center-middle" rowspan="{rowspan}" colspan="3">
                    Order {order['ORDER_NUMBER']} - Placed: {datetime.strftime(order['ORDER_DATE'], '%b %d, %Y')}
                    </br>
                    Store: {order['GEO']} - Status: {order['FINANCIAL_STATUS']}
                    </br>
                    Total: {order['TOTAL']} {order['CURRENCY']} - Discounts: {order['DISCOUNT']} {order['CURRENCY']}
                </td>
            """

    for l in items:
        if l['REFUND_QUANTITY'] == l['QUANTITY']:
            financial_status = 'Fully Refunded'
        elif l['REFUND_QUANTITY'] >= 1:
            financial_status = f"{l['REFUND_QUANTITY']} of {l['QUANTITY']} Refunded"
        else:
            financial_status = l['ORDER_FINANCIAL_STATUS']

        if l['TRACKING_COMPANY'] is not None:
            logistics_string = f"Shipped {datetime.strftime(l['SHIPPED_AT'], '%b %d, %Y')} - {l['SHIPMENT_STATUS']}</br>{l['TRACKING_COMPANY']}: {l['TRACKING_NUMBER']}"
        else:
            logistics_string = 'No Shipping Record'

        html += f"""
                    <td class="center-middle" colspan="2">{l['PRODUCT']}</td>
                    <td class="center-middle">unknown</td>
                    <td class="center-middle">{l['FULFILLMENT_STATUS']}</td>
                    <td class="center-middle">{financial_status}</td>
                    <td class="center-middle" colspan="2">{logistics_string}</td>
                </tr>
        """

    return html


def make_dtc_order_detail(lines):
    if len(lines.keys()) == 0:
        return ''
    body = ''
    for k, o in lines.items():
        body += make_row(o, o['LINES'])
    return f"""
        <tr class="black-header">
                <td class="center-middle" colspan="3">Order Details</td>
                <td class="center-middle" colspan="2">Items</td>
                <td class="center-middle">Serial</td>
                <td class="center-middle">Fulfillment</td>
                <td class="center-middle">Financial</td>
                <td class="center-middle" colspan="2">Shipping Out</td>
            </tr>
    """ + body