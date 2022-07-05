def get_dtc_orders(customer_ids: [str], geos: [str], connection:{}) -> [[{any}], [str]]:
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
    dtc_orders = connection.get_data("snowflake", query=dtc_query, return_mapped=True)
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