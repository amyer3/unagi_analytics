from datetime import datetime


def map_to_rows(subscription, slots: []) -> str:
    rowspan = len(slots) if len(slots) > 1 else 1
    if subscription['STATUS'] == 'voided' or subscription['STATUS'] == 'early cancel' or subscription['STATUS'] == 'void':
        return f"""
        <tr class="red-row">
            <td class="center-middle">{subscription['ID']}</td>
            <td class="center-middle">{subscription['STATUS']}</td>
            <td class="center-middle">{datetime.strftime(subscription['START_DATE'], '%b %d, %Y')}</td>
            <td class="center-middle">{datetime.strftime(subscription['ENDED_AT'], '%b %d, %Y')}</td>
            <td class="center-middle" colspan="6">DO NOT OPEN NEW SUBSCRIPTION. CUSTOMER INELIGIBILE FOR ALL ACCESS, MUST
                BUY SCOOTER VIA DTC:unagiscooters.com/checkout/configure/
            </td>
        </tr>
        """
    if subscription['ENDED_AT'] is None or subscription['ENDED_AT'] == '':
        subscription['ENDED_AT'] = ''
    else:
        subscription['ENDED_AT'] = datetime.strftime(subscription['ENDED_AT'], '%b %d, %Y')
    subs = f"""
        <tr>
            <td class="center-middle" rowspan="{rowspan}">{subscription['ID']}</td>
            <td class="center-middle" rowspan="{rowspan}">{subscription['STATUS']}</td>
            <td class="center-middle" rowspan="{rowspan}">{datetime.strftime(subscription['START_DATE'], '%b %d, %Y')}</td>
            <td class="center-middle" rowspan="{rowspan}">{subscription['ENDED_AT']}</td>
        """
    if len(slots) == 0:
        subs += '<td class="center-middle" colspan="6">No slots / logistics found for this subscription.</td>'
    else:
        slots = sorted(slots, key=lambda x: x['index'], reverse=True)
        for row in slots:
            outbound_logistic_string = f"""
            Shipped { datetime.strftime(row['outbound_created_at'], '%b %d, %Y') if row['outbound_created_at'] is not None else 'pending'} 
            <br> 
            {"Delivered: " + datetime.strftime(row['outbound_completed_at'], '%b %d, %Y') if row['outbound_completed_at'] is not None else 'NOT DELIVERED'}
            <br>
            {row['outbound_logistic']}: {row['outbound_tracking']}
            """
            inbound_logistic_string = f"""
            Shipped {datetime.strftime(row['inbound_created_at'], '%b %d, %Y') if row['inbound_created_at'] is not None else 'pending'} 
            <br> 
            {"Delivered: " +datetime.strftime(row['inbound_completed_at'], '%b %d, %Y')  if row['inbound_completed_at'] is not None else 'NOT DELIVERED'}
            <br>
            {row['inbound_logistic']}: {row['inbound_tracking']}
            """ if row['inbound_tracking'] is not None else ''
            subs += f"""
                <td class="center-middle">{row['slot_id']}</td>
                <td class="center-middle">{row['product_id'] or 'unknown'}</td>
                <td class="center-middle">{row['status']}</td>
                <td class="center-middle">{row['sub_update_type']}</td>
                <td class="center-middle">{outbound_logistic_string}</td>
                <td class="center-middle">{inbound_logistic_string}</td>
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
       <td class="center-middle">Sub ID</td>
       <td class="center-middle">Status</td>
       <td class="center-middle">Start</td>
       <td class="center-middle">End</td>
       <td class="center-middle">Slot ID</td>
       <td class="center-middle">Serial</td>
       <td class="center-middle">Slot Status</td>
       <td class="center-middle">Reason</td>
       <td class="center-middle">Shipping Out</td>
       <td class="center-middle">Shipping In</td>
    </tr>
    """ + b
