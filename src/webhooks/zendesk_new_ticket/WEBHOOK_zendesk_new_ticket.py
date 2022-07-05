import datetime, requests, json
from src.services import connection_manager as cm
from make_html_body import make_html
from data_sources.get_subscription_logistics import get_subscription_logistics
from data_sources.get_subscription_orders import get_subscription_orders
from data_sources.get_dtc_orders import get_dtc_orders
from data_sources.get_all_customers import get_all_customers

c = cm.Connection()

USERNAME = 'alex.myers@unagiscooters.com/token'
TOKEN = 'AVeITAD0b4fPhkfIKLQE8r8bEttL9mDQLaaLtpWU'


def clean_phone(phone: any) -> str:
    return str(phone).replace(')', '').replace('(', '').replace('-', '').replace(' ', '')[4:]


def search_and_update(ticket_id: int, conenction={}, **kwargs):
    updated_at = datetime.datetime.strftime(datetime.datetime.now(), '%B %m, %Y at %R UTC')
    phone_c = clean_phone(kwargs['phone']) if 'phone' in kwargs else '9999999999999999999999999'
    email_c = kwargs['email'] if 'email' in kwargs else '9999999999999999999999999'
    customer_data = get_all_customers(phone_c, email_c, c)
    # COLUMNS COME BACK UPPERCASED
    # columns, rows come back as tuples
    if len(customer_data['data']) == 0:
        # return just the header
        return

    geos_u = []
    ids = {}
    custe = {}
    for r in customer_data['data']:
        t = {}
        for i, v in enumerate(r):
            t[customer_data['columns'][i]] = v
        custe[r[0]] = t

    # loop through customer details, and propigate a list of product/customer ID's and geographies
    for i, (k, v) in enumerate(custe.items()):
        if phone_c not in clean_phone(v['PHONE']) or email_c != v['EMAIL']:
            continue
        if v['PRODUCT'] not in ids:
            ids[v['PRODUCT']] = []
        if v['GEO'] not in geos_u:
            geos_u.append(v['GEO'])
        if v['ID'] not in ids[v['PRODUCT']]:
            ids[v['PRODUCT']].append(v['ID'])

    dtc_orders = get_dtc_orders(ids['dtc'], geos_u, c)
    sub_orders = get_subscription_orders(ids['allaccess'], c)

    subscriptions, shipments = {}, []
    if len(sub_orders[0]) > 0:
        shipments = get_subscription_logistics(map(lambda x: x[0], sub_orders[0]), c)

    for s in sub_orders[0]:
        this_id = s[0]
        t = {}
        for i, v in enumerate(s):
            if this_id == 'sub_1K49OPJ9uHP6DArCw5xrsGSx' and sub_orders[1][i] == 'STATUS': v = 'void'
            t[sub_orders[1][i]] = v if v is not None else ''
        t['slot'] = []
        subscriptions[this_id] = t

    if len(shipments[0]) > 0:
        for l in shipments[0]:
            t = {}
            for i, v in enumerate(l):
                t[shipments[1][i]] = v
            subscriptions[t['sub_id']]['slot'].append(t)

    html = make_html(time=updated_at, sub_data=subscriptions, dtc_data=dtc_orders, customer_data=custe)
    print(html)
    request_body = {
        "ticket": {
            'status': 'open',
            "comment": {
                "html_body": html,
                "public": False
            }
        }
    }
    url = f"https://unagiscooters.zendesk.com/api/v2/tickets/{str(ticket_id)}.json"
    try:
        # requests API does not support / like json.dumps(request_body) for some reason
        response = requests.put(url, json=request_body, auth=(USERNAME, TOKEN))
    except Exception:
        pass
    return 200

