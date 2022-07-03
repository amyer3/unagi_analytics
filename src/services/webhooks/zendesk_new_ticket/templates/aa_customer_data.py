from datetime import datetime
def make_row(customer):
    return f"""
        <tr>
            <td class="center-middle">{customer['ID'] or ''}</td>
            <td class="center-middle">{customer['NAME'] or ''}</td>
            <td class="center-middle">{datetime.strftime(customer['CREATED'], '%b %d, %Y') or ''}</td>
            <td class="center-middle" colspan="4">{customer['ADDRESS']}</td>
            <td class="center-middle">{customer['PHONE'] or ''}</td>
            <td class="center-middle">{customer['EMAIL'] or ''}</td>
            <td class="center-middle">{''}</td>
        </tr>
    """


def make_aa_customer_data(customer_data: {}) -> str:
    if len(customer_data) == 0:
        return ''
    c = []
    for i, (k, v) in enumerate(customer_data.items()):
        if v['PRODUCT'] == 'allaccess':
            c.append(v)
    c = sorted(c, key=lambda row: row['CREATED'], reverse=True)
    #{'ID': 'cus_LxKdWGqkSO3bQt', 'CREATED': datetime.datetime(2022, 6, 27, 22, 0, 10, tzinfo=<UTC>), 'NAME': 'Kyle Robertson', 'DELINQUENT': False, 'EMAIL': 'kyle+test@unagiscooters.com', 'PHONE': '4087053642', 'PRODUCT': 'allaccess', 'GEO': 'USA', 'METADATA': '{\n  "fbp": "fb.1.1656351518829.939685942",\n  "siftSessionId": "_ozpuqgo9w1656450148256",\n  "subscription_region": "LA"\n}'}
    b=''
    for i in c:
        b+=make_row(i)
    return f"""
        <tr>
            <td class="center-middle" colspan="10">All Access (stripe)</td>
        </tr>
        <tr class="black-header">
            <td class="center-middle b">Customer ID</td>
            <td class="center-middle">Name</td>
            <td class="center-middle">Created</td>
            <td class="center-middle" colspan="4">Address</td>
            <td class="center-middle">Phone</td>
            <td class="center-middle">Email</td>
            <td class="center-middle">Partner</td>
        </tr>
        {b}
        <tr>
            <td class="center-middle" colspan="10"></td>
        </tr>
        """