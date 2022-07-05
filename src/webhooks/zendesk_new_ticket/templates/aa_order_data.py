from datetime import datetime


def map_to_rows(subscription, slots: []) -> str:
    rowspan = len(slots) if len(slots) > 1 else 1
    if subscription['ENDED_AT'] is None or subscription['ENDED_AT'] == '':
        subscription['ENDED_AT'] = 'n/a'
    else:
        subscription['ENDED_AT'] = datetime.strftime(subscription['ENDED_AT'], '%b %d, %Y')

    if subscription['STATUS'] == 'voided' or subscription['STATUS'] == 'void':
        return f"""
        <tr class="red-row">
            <td colspan="3">{subscription['ID']}<br>open: {datetime.strftime(subscription['START_DATE'], '%b %d, %Y')} | close: {subscription['ENDED_AT']}</td>
            <td>{subscription['STATUS']}</td>
            <td colspan="6">DO NOT OPEN NEW SUBSCRIPTION. CUSTOMER INELIGIBILE FOR ALL ACCESS, MUST
                BUY VIA DTC: unagiscooters.com/checkout/configure
            </td>
        </tr>
        """
    subs = f"""
        <tr>
            <td colspan="3" rowspan={rowspan}>{subscription['ID']}<br>open: {datetime.strftime(subscription['START_DATE'], '%b %d, %Y')} | close: {subscription['ENDED_AT']}</td>
            <td class="center-middle" rowspan="{rowspan}">{subscription['STATUS']}</td>
        """
    if len(slots) == 0:
        subs += '<td class="center-middle" colspan="6">No slots / logistics found for this subscription.</td>'
    else:
        slots = sorted(slots, key=lambda x: x['index'], reverse=True)
        for row in slots:
            outbound_logistic_string = f"""
            Sent: { datetime.strftime(row['outbound_created_at'], '%b %d, %Y') if row['outbound_created_at'] is not None else 'NOT SENT'} 
            <br> 
            {"Rec'd: " + datetime.strftime(row['outbound_completed_at'], '%b %d, %Y') if row['outbound_completed_at'] is not None else 'NOT DELIVERED'}
            <br>
            {row['outbound_logistic']} {row['outbound_tracking']}
            """

            inbound_logistic_string = f"""
            Sent: {datetime.strftime(row['inbound_created_at'], '%b %d, %Y') if row['inbound_created_at'] is not None else 'NOT SENT'} 
            <br> 
            {"Rec'd: " +datetime.strftime(row['inbound_completed_at'], '%b %d, %Y')  if row['inbound_completed_at'] is not None else 'NOT DELIVERED'}
            <br>
            {row['inbound_logistic']} {row['inbound_tracking']}
            """ if row['inbound_tracking'] is not None else ''

            subs += f"""
                <td colspan="3">{row['slot_id']} | SN: {row['product_id']}<br>status: {row['status']} | type: {row['sub_update_type']}</td>
                <td>{row['product_id'] or 'unknown'}</td>
                <td>{outbound_logistic_string}</td>
                <td>{inbound_logistic_string}</td>
            </tr>
            """
    return subs


def make_aa_order_data(sub_orders):
    if len(sub_orders.keys()) == 0:
        return ''
    # for sub in subs, return map_to_rows(sub_orders)
    c = []
    for i, (k, v) in enumerate(sub_orders.items()):
        v['PARTNER'] = str(v['PARTNER']).replace('partner:', '')
        c.append(v)
    c = sorted(c, key=lambda row: row['START_DATE'], reverse=True)
    b = ''
    for i in c:
        b += map_to_rows(i, i['slot'] if i['slot'] is not None else [])
    return f"""
    <tr class="black-header">
       <td colspan="3">Stripe Sub ID & Dates</td>
       <td>Status</td>
       <td colspan="3">Slot Details</td>
       
       
       <td class="center-middle">Serial</td>
       <td class="center-middle">Shipping Out</td>
       <td class="center-middle">Shipping In</td>
    </tr>
    """ + b
