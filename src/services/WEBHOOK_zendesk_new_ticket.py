import datetime, threading
from connection_manager import Connection
from webhooks.zendesk_new_ticket.make_html_body import make_html

"""
https://unagiscooters.zendesk.com/api/v2/tickets/{TICKET ID #}.json
"""
c = Connection()


def clean_phone(phone: any) -> str:
    return str(phone).replace(')', '').replace('(', '').replace('-', '').replace(' ', '')[4:]


def get_dtc_orders(customer_ids: [str], geos: [str]) -> [[{any}], [str]]:
    customer_id_string = ','.join(customer_ids) if len(customer_ids) > 1 else customer_ids[0]
    geo_string = ','.join(geos) if len(geos) > 1 else "'" + geos[0] + "'"
    dtc_query = f"""SELECT
  li.LINE_DESC,
  li.line_id,
  line_title             AS product,
  li.quantity,
  li.fulfillment_status,
  total_discount,
  order_total,
  li.cancelled_at,
  li.closed_at,
  li.cancel_reason,
  li.confirmed,
  o.GEO as GEO,
  f.tracking_urls as tracking_url,
  fulfillment_date::date AS shipped_at,
  refund_quantity,
  refund_subtotal,
  refund_reason,
  product_type,
  line_discount,
  f.SHIPMENT_STATUS,
  f.TRACKING_COMPANY,
  f.TRACKING_NUMBER,
  o.id as order_id,
  note,
  total_price,
  o.created_at::date     AS order_date,
  o.name                 AS order_number,
  o.financial_status as order_financial_status,
  o.total_price as order_total,
  o.currency,
  o.total_discounts as order_discounts,
  total_discounts
FROM WW_DTC_LINE_ITEMS li
INNER JOIN (
			 SELECT
			   *,
			   'USA' AS geo
			 FROM FIVETRAN_US_SHOPIFY."ORDER"
			 UNION
			 SELECT
			   *,
			   'EUR' AS geo
			 FROM FIVETRAN_EU_SHOPIFY."ORDER"
			 UNION
			 SELECT
			   *,
			   'CAN' AS geo
			 FROM FIVETRAN_CA_SHOPIFY."ORDER"
			 UNION
			 SELECT
			   *,
			   'UK' AS geo
			 FROM FIVETRAN_UK_SHOPIFY."ORDER"
			 UNION
			 SELECT
			   *,
			   'AUS' AS geo
			 FROM FIVETRAN_AU_SHOPIFY."ORDER"
		   )           o ON o.NAME = li.ORDER_NO AND o.CUSTOMER_ID IN ({customer_id_string}) AND o.geo IN ({geo_string})
INNER JOIN (
			 SELECT
			   *,
			   'USA' AS geo
			 FROM FIVETRAN_US_SHOPIFY.FULFILLMENT_ORDER_LINE
			 UNION
			 SELECT
			   *,
			   'EUR' AS geo
			 FROM FIVETRAN_EU_SHOPIFY.FULFILLMENT_ORDER_LINE
			 UNION
			 SELECT
			   *,
			   'CAN' AS geo
			 FROM FIVETRAN_CA_SHOPIFY.FULFILLMENT_ORDER_LINE
			 UNION
			 SELECT
			   *,
			   'UK' AS geo
			 FROM FIVETRAN_UK_SHOPIFY.FULFILLMENT_ORDER_LINE
			 UNION
			 SELECT
			   *,
			   'AUS' AS geo
			 FROM FIVETRAN_AU_SHOPIFY.FULFILLMENT_ORDER_LINE
		   )           fol ON fol.ORDER_LINE_ID = li.LINE_ID AND fol.geo IN ({geo_string})
INNER JOIN (
			 SELECT
			   *,
			   'USA' AS geo
			 FROM FIVETRAN_US_SHOPIFY.FULFILLMENT
			 UNION
			 SELECT
			   *,
			   'EUR' AS geo
			 FROM FIVETRAN_EU_SHOPIFY.FULFILLMENT
			 UNION
			 SELECT
			   *,
			   'CAN' AS geo
			 FROM FIVETRAN_CA_SHOPIFY.FULFILLMENT
			 UNION
			 SELECT
			   *,
			   'UK' AS geo
			 FROM FIVETRAN_UK_SHOPIFY.FULFILLMENT
			 UNION
			 SELECT
			   *,
			   'AUS' AS geo
			 FROM FIVETRAN_AU_SHOPIFY.FULFILLMENT
		   )           f ON f.id = fol.FULFILLMENT_ID AND f.geo IN ({geo_string})
"""
    dtc_orders = c.get_data("snowflake", query=dtc_query, return_mapped=True)
    # COLUMNS COME BACK UPPERCASED
    orders = {}
    for r in dtc_orders:
        on = r['ORDER_NUMBER']
        if on not in orders:
            # every order must be made up of at least 1 line item, otherwise there's no order
            # if the dict doesn't have a record for this order number, pull the order level metadata
            # out of the first order line that comes up, and populate the metadata based on that.
            orders[on] = {
                'ORDER_DATE': r['ORDER_DATE'],
                'ORDER_NUMBER': r['ORDER_NUMBER'],
                'FINANCIAL_STATUS': r['ORDER_FINANCIAL_STATUS'],
                'TOTAL': r['ORDER_TOTAL'],
                'DISCOUNT': r['TOTAL_DISCOUNTS'],
                'CURRENCY': r['CURRENCY'],
                'GEO': r['GEO'],
                "LINES": [
                    r
                ]
            }
        else:
            orders[on]['LINES'].append(r)
    return orders


def get_subscription_orders(customer_ids: [str]) -> [[{any}], [str]]:
    # get all subscription records for this customer
    # THEN, clean the array to pull all slot records for each subscription ID
    # THEN clean and pull most recent INBOUND and OUTBOUND records for each slot
    customer_id_string = ','.join("'%s'" % i for i in customer_ids)
    sub_query = f"""select s.id, s.start_date, s.ended_at, d.most_recent_status as status, d.partner from fivetran_stripe.subscription s
         inner join FIVETRAN_STRIPE.SUB_DAILY d on s.id = d.SUB_ID and d._KEY = true 
         where s.CUSTOMER_ID in ({customer_id_string})"""
    sub_orders = c.get_data("snowflake", query=sub_query)
    return [sub_orders['data'],
            sub_orders['columns']]


def get_subscription_logistics(subscription_ids: [str]) -> any:
    sub_id_string = ','.join("'%s'" % i for i in subscription_ids)
    logi_query = f"""with inbound as ( select
					   l.created_at,
					   l.completed_at,
					   coalesce(l.tracking_number, l.onfleet_id) as tracking,
					   l.order_id                                as slot_id,
					   l.product_id,
					   l.status,
					   l.logistic_method,
					   l.direction,
					   l.sub_update_type
				from logistics l
				where l.status <> 'void' and (l.void_reason is null or l.void_reason ='') and l.product_type = 'scooter' and direction like '%inbound%'),
   outbound as ( select
					   l.created_at,
					   l.completed_at,
					   coalesce(l.tracking_number, l.onfleet_id) as tracking,
					   l.order_id                                as slot_id,
					   l.product_id,
					   l.status,
					   l.logistic_method,
					   l.direction,
					   l.sub_update_type
				from logistics l
				where l.status <> 'void' and (l.void_reason is null or l.void_reason ='') and l.product_type = 'scooter' and direction like '%outbound%')
select
  distinct s.id as slot_id,
  s.index,
  s.sub_id,
  s.status as status,
  o.product_id as product_id,
  o.sub_update_type as sub_update_type,
  o.created_at as outbound_created_at,
  o.completed_at as outbound_completed_at,
  coalesce(o.tracking, '') as outbound_tracking,
  coalesce(o.logistic_method, '') as outbound_logistic,
  i.created_at as inbound_created_at,
  i.completed_at as inbound_completed_at,
  i.tracking as inbound_tracking,
  i.logistic_method as inbound_logistic
from slot s
left join outbound o on s.id = o.slot_id
left join inbound i on i.slot_id = o.slot_id
 where s.status <> 'void' and s.sub_id in ({sub_id_string})"""
    logi = c.get_data('postgres', logi_query)
    return [logi['data'],
            logi['columns']]


def search_and_update(conenction={}, **kwargs):
    updated_at = datetime.datetime.strftime(datetime.datetime.now(), '%B %m, %Y at %R UTC')
    phone_c = clean_phone(kwargs['phone']) if 'phone' in kwargs else '9999999999999999999999999'
    email_c = kwargs['email'] if 'email' in kwargs else '9999999999999999999999999'
    get_all_customers = f"select * from all_customers where (email = '{email_c}' or PHONE::text like '%{phone_c}')"
    customer_data = c.get_data('snowflake', get_all_customers)
    # COLUMNS COME BACK UPPERCASED
    # columns, rows come back as tuples
    if len(customer_data['data']) == 0:
        # return just the header
        return

    geos_u = []
    ids = {}
    custe = {}
    for r in customer_data['data']:
        id = r[0]
        t = {}
        for i, v in enumerate(r):
            t[customer_data['columns'][i]] = v
        custe[id] = t

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

    dtc_orders = get_dtc_orders(ids['dtc'], geos_u)
    """
    [
    id: text, 
    status: text, 
    opened_at: mm/dd/yyyy text,
    closed_at: mm/dd/yyyy text,
    slots: {
            id{
                inbound:{
                id: text, 
                product_id: text,
                status: text,
                sub_update_type: text,
                created_at: mm/dd/yyyy text,
                delivered_at: mm/dd/yyyy text,
                logistic_method: text,
                tracking: text
            },
            outbound:{...}
            }
            
        }
    ]
    """
    sub_orders = get_subscription_orders(ids['allaccess'])
    subscriptions = {}
    shipments = []
    if len(sub_orders[0]) > 0:
        shipments = get_subscription_logistics(map(lambda x: x[0], sub_orders[0]))

    for s in sub_orders[0]:
        this_id = s[0]
        t = {}
        for i, v in enumerate(s):
            if s[0] == 'sub_1KkibYJ9uHP6DArCR4SdNQlY' and sub_orders[1][i] == 'STATUS':
                v ='voided'
            t[sub_orders[1][i]] = v if v is not None else ''
        t['slot'] = []
        subscriptions[this_id] = t

    if len(shipments[0]) > 0:
        for l in shipments[0]:
            t = {}
            for i, v in enumerate(l):
                t[shipments[1][i]] = v
            subscriptions[t['sub_id']]['slot'].append(t)
    print(subscriptions)
    html =make_html(time=updated_at, sub_data=subscriptions, dtc_data=dtc_orders, customer_data=custe)
    print(html)


if __name__ == '__main__':
    search_and_update(phone='4087053642', email='kyle@unagiscooters.com')
