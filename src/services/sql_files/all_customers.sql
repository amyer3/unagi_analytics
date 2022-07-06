-- select * from FACEBOOK_ADS_INSIGHTS.CREATIVE_HISTORY
--          where PAGE_LINK like '%unagiscooters.com%'
--          order by _FIVETRAN_SYNCED desc
WITH
  shopify AS (
			   SELECT
				 *, 'USA' as geo
			   FROM FIVETRAN_US_SHOPIFY.CUSTOMER
			   UNION
			   SELECT
				 *, 'EUR' as geo
			   FROM FIVETRAN_EU_SHOPIFY.CUSTOMER
			   UNION
			   SELECT
				 *, 'CAN' as geo
			   FROM FIVETRAN_CA_SHOPIFY.CUSTOMER
			   UNION
			   SELECT
				 *, 'UK' as geo
			   FROM FIVETRAN_UK_SHOPIFY.CUSTOMER
			   UNION
			   SELECT
				 *, 'AUS' as geo
			   FROM FIVETRAN_AU_SHOPIFY.CUSTOMER
			 )
SELECT
  id,
  created,
  name,
  DELINQUENT,
  lower(email) as email,
  COALESCE(PHONE, shipping_phone) as phone,
--   INVOICE_PREFIX,
--   SHIPPING_ADDRESS_CITY,
--   SHIPPING_ADDRESS_COUNTRY,
--   SHIPPING_ADDRESS_LINE_1,
--   SHIPPING_ADDRESS_LINE_2,
--   SHIPPING_ADDRESS_POSTAL_CODE,
--   SHIPPING_ADDRESS_STATE,
  'allaccess' AS product,
  'USA' as geo
FROM FIVETRAN_STRIPE.CUSTOMER
UNION
select
  id::text,
  CREATED_AT,
  FIRST_NAME || ' ' || LAST_NAME as name,
  null,
  lower(EMAIL),
  PHONE,
  'dtc' as product,
  geo
from shopify