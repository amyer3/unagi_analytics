from datetime import datetime
def make_row(customer):
    return f"""
        <tr>
            <td class="center-middle" colspan="2">{customer['NAME']} ({customer['ID']})</td>
            <td class="center-middle" colspan="5">{customer['ADDRESS']}</td>
            <td class="center-middle">{customer['PHONE'] or ''}</td>
            <td class="center-middle">{customer['EMAIL'] or ''}</td>
            <td class="center-middle">{''}</td>
        </tr>
    """


def make_dtc_customer_data(customer_data: {}) -> str:
    if len(customer_data) == 0:
        return ''
    c = []
    for i, (k, v) in enumerate(customer_data.items()):
        if v['PRODUCT'] == 'dtc':
            c.append(v)
    c = sorted(c, key=lambda row: row['CREATED'], reverse=True)
    #{'ID': 'cus_LxKdWGqkSO3bQt', 'CREATED': datetime.datetime(2022, 6, 27, 22, 0, 10, tzinfo=<UTC>), 'NAME': 'Kyle Robertson', 'DELINQUENT': False, 'EMAIL': 'kyle+test@unagiscooters.com', 'PHONE': '4087053642', 'PRODUCT': 'allaccess', 'GEO': 'USA', 'METADATA': '{\n  "fbp": "fb.1.1656351518829.939685942",\n  "siftSessionId": "_ozpuqgo9w1656450148256",\n  "subscription_region": "LA"\n}'}
    b=''
    for i in c:
        b+=make_row(i)
    return f"""
        <tr>
            <td colspan="10">DTC Orders (shopify)</td>
        </tr>
        <tr class="black-header">
            <td colspan="2">Customer Name (Shopify ID)</td>
            <td colspan="5">Address</td>
            <td>Phone</td>
            <td>Email</td>
            <td>Partner</td>
        </tr>
        {b}
        <tr>
            <td colspan="10"></td>
        </tr>
        """