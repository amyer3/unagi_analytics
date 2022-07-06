with days as (
    select seq4()                                                               as idx,
           dateadd(day, seq4(), '2020-08-01 00:00:00 +000'::timestamp_tz)::date as action_date
    from table (generator(rowcount => 5000)) as v
),
     subs as (select li.unique_id,
                     li.amount,
                     inv.SUBSCRIPTION_ID                             as subscription_id,
                     li.quantity                                     as qty,
                     inv.subscription_id                             as sub_id,
                     iff(inv.status_transitions_paid_at is not null, inv.status_transitions_paid_at,
                         chg.created)::date                          as paid_at,
                     -- needs to be rolled forward a day so that there's no overlap between periods
                     iff(inv.billing_reason like '%create', li.PERIOD_START::date,
                         dateadd(day, 1, li.PERIOD_START::date))     as period_start,
                     li.period_end::date                             as period_end,
                     inv.billing_reason,
                     sub.ended_at::date                              as canceled_at,
                     inv.status                                      as inv_status,
                     li.type                                         as item_type,
                     inv.id                                          as invoice_id,
                  /*  */
                     dateadd(day, 15, inv.created::date)             as past_due_at,
                     dateadd(day, 28, inv.created::date)             as unpaid_at,
                     dateadd(day, 90, inv.created::date)             as decay_at,
                  /*  */
                     chg.refunded                                    as is_refunded,
                     prod.name                                       as prod_name,
                     datediff(MONTH, li.period_start, li.period_end) as months_purchased,
                     inv.attempted,
                     r.reason                                        as refund_reason,
                     date_trunc(day, r.created)                      as refunded_at,
                     li.period_end::date                             as orig_end,
                     li.period_start::date                           as orig_start,
                     sub.start_date                                  as subscription_start,
                     regexp_substr(replace(replace(cust.METADATA, '"', ''), ' ', ''),
                                   'partner:[a-zA-Z0-9-]*')          as partner,
                     (case
                          when STATUS_TRANSITIONS_VOIDED_AT is not null
                              then dateadd(day, 1, STATUS_TRANSITIONS_VOIDED_AT)
                          when sub.ENDED_AT < li.PERIOD_END then dateadd(day, 1, sub.ENDED_AT)
                          when STATUS_TRANSITIONS_PAID_AT::date > li.PERIOD_END::date then STATUS_TRANSITIONS_PAID_AT
                          when inv.PAID = true then li.PERIOD_END
                          when inv.PAID = false then dateadd(day, 91, inv.created)
                         end)::date                                  as adjusted_end_date
              from FIVETRAN_STRIPE.INVOICE_LINE_ITEM as li
                       left join FIVETRAN_STRIPE.INVOICE as inv on inv.id = li.invoice_id
                       left join FIVETRAN_STRIPE.PRICE as price on price.id = li.plan_id
                       left join FIVETRAN_STRIPE.PRODUCT as prod on prod.id = price.product_id

                  -- some invoices are 'draft' status, but have valid charges point to them,
                  -- with no record of the charge ID on the invoice record
                  -- seen mostly in OCT 2021
                  -- normalize charge records, providing a consistent join
                  -- one join on charge_id = invoice_charge_id, get invoice_id
                  -- if that's null, then fall back to using invoice_id from charge table
                       left join FIVETRAN_STRIPE.SUBSCRIPTION as sub on sub.id = inv.subscription_id
                       left join FIVETRAN_STRIPE.CUSTOMER as cust on cust.id = sub.CUSTOMER_ID
                       left join (
                  select c.id,
                         c.captured,
                         c.created,
                         c.paid,
                         c.refunded,
                         IFF(i.id is null, c.invoice_id, i.id) as invoice_id
                  from FIVETRAN_STRIPE.CHARGE as c
                           left join fivetran_stripe.invoice as i on i.charge_id = c.id
                  where c.status = 'succeeded'
              ) as chg on chg.invoice_id = inv.id
                  /*  */
                       left join fivetran_stripe.refund as r on r.charge_id = chg.id
              where li.type = 'subscription'
                and li.livemode = TRUE
                and prod.METADATA like '%all access%'
                and cust.IS_DELETED = false
                and case
                        when inv.status = 'draft' and chg.paid then TRUE
                        when inv.status = 'draft' and not chg.paid then FALSE
                        when inv.status <> 'draft' then TRUE
                  end
                and billing_reason <> 'subscription_update'
                and (
                  case
                      when billing_reason <> 'subscription_create'
                          and inv.status = 'void' then FALSE
                      when billing_reason = 'subscription_create'
                          and paid_at is null then FALSE
                      else TRUE
                      end
                  )),
     mri as (
         select distinct SUBSCRIPTION_ID,
                         max(period_end) over (partition by subscription_id) as period_end
         from subs
     ),
     statuses as (
         select action_date,
                CASE
                    when paid_at is not null
                        and action_date >= paid_at then case
                        /* all voids are paid, refunded, and have refund code of fraudulent */
                                                            when subs.billing_reason =
                                                                 'subscription_create'
                                                                and refund_reason =
                                                                    'fraudulent'
                                                                and
                                                                 action_date >=
                                                                 refunded_at
                                                                then 'voided'
                        /* if this isn't refunded for fraud, and is canceled, and is paid, then it's canceled */
                                                            when subs.canceled_at is not null
                                                                and
                                                                 action_date >=
                                                                 subs.canceled_at
                                                                then 'canceled'
                        /*  */
                                                            when (
                                                                        action_date <
                                                                        subs.canceled_at
                                                                    or
                                                                        subs.canceled_at is null
                                                                ) then 'active'
                        end
                    /* if this invoice isn't paid (or isn't paid yet),
                       cycle through delinquency until we get to paid / decay
                     */
                    when paid_at is null
                        OR action_date < paid_at then case
                                                          when action_date < past_due_at
                                                              then 'grace period'
                                                          when action_date between past_due_at and unpaid_at
                                                              then 'unpaid'
                                                          when action_date between unpaid_at and decay_at
                                                              then 'past due'
                                                          when action_date >= decay_at
                                                              then 'decay'
                        end
                    END                                                                          as day_status,
                lag(day_status, 1) over (partition by subs.subscription_id order by action_date) as prev_status,
                iff(mri.period_end is not null, TRUE, FALSE)                                     as most_recent_invoice,
                row_number() over (partition by sub_id order by action_date)                     as days_active,
                action_date = subscription_start::date                                           as key,
                subs.*
         from days
                  left join subs on days.action_date between subs.PERIOD_START and subs.adjusted_end_date
                  left join mri on mri.period_end = subs.period_end and subs.subscription_id = mri.subscription_id
         where action_date <= dateadd(day, 30, current_date)),
     us_orders as (
/*
***** US ORDERS *****
 */
         select ol.id                          as line_id,
                ol.name                        as line_desc,
                ol.title                       as line_title,
                ol.price                       as price,
                ol.quantity,
                ol.fulfillment_status,
                o.currency,
                o.created_at::date             as created_at,
                o.name                         as order_no,
                o.shipping_address_country_code,
                o.shipping_address_province_code,
                o.shipping_address_latitude    as latitude,
                o.shipping_address_longitude   as longitude,
                o.processing_method,
                o.cancelled_at,
                o.closed_at,
                o.cancel_reason,
                o.confirmed,
                f.status                       as f_status,
                f.tracking_company,
                f.shipment_status,
                olr.quantity                   as refund_quantity,
                olr.subtotal                   as refund_subtotal,
                prod.title                     as product_name,
                trim(upper(prod.PRODUCT_TYPE)) as product_type,
                t.status                       as payment_status,
                pv.option_1,
                pv.option_2,
                pv.option_3,
                'USA'                          as geo
         from fivetran_us_shopify.order_line as ol
                  left join unagi_edw.fivetran_us_shopify."ORDER" as o on o.id = ol.order_id
                  left join fivetran_us_shopify.fulfillment_order_line as fol on fol.order_line_id = ol.id
                  left join fivetran_us_shopify.order_line_refund as olr on olr.order_line_id = ol.id
                  left join fivetran_us_shopify.fulfillment as f on f.id = fol.fulfillment_id
                  left join fivetran_us_shopify.product as prod on prod.id = ol.product_id
                  left join fivetran_us_shopify.transaction as t on t.order_id = o.id
                  left join fivetran_us_shopify.product_variant as pv on pv.product_id = ol.variant_id
     ),
     eu_orders as (
/*
***** EUROPEAN ORDERS *****
 */
         select ol.id                          as line_id,
                ol.name                        as line_desc,
                ol.title                       as line_title,
                ol.price                       as price,
                ol.quantity,
                ol.fulfillment_status,
                o.currency,
                o.created_at::date             as created_at,
                o.name                         as order_no,
                o.shipping_address_country_code,
                o.shipping_address_province_code,
                o.shipping_address_latitude    as latitude,
                o.shipping_address_longitude   as longitude,
                o.processing_method,
                o.cancelled_at,
                o.closed_at,
                o.cancel_reason,
                o.confirmed,
                f.status                       as f_status,
                f.tracking_company,
                f.shipment_status,
                olr.quantity                   as refund_quantity,
                olr.subtotal                   as refund_subtotal,
                prod.title                     as product_name,
                trim(upper(prod.PRODUCT_TYPE)) as product_type,
                t.status                       as payment_status,
                pv.option_1,
                pv.option_2,
                pv.option_3,
                'EU'                           as geo
         from fivetran_eu_shopify.order_line as ol
                  left join unagi_edw.fivetran_eu_shopify."ORDER" as o on o.id = ol.order_id
                  left join fivetran_eu_shopify.fulfillment_order_line as fol on fol.order_line_id = ol.id
                  left join fivetran_eu_shopify.order_line_refund as olr on olr.order_line_id = ol.id
                  left join fivetran_eu_shopify.fulfillment as f on f.id = fol.fulfillment_id
                  left join fivetran_eu_shopify.product as prod on prod.id = ol.product_id
                  left join fivetran_eu_shopify.transaction as t on t.order_id = o.id
                  left join fivetran_eu_shopify.product_variant as pv on pv.product_id = ol.variant_id
     ),
     au_orders as (
/*
***** AUSTRALIAN ORDERS *****
 */
         select ol.id                          as line_id,
                ol.name                        as line_desc,
                ol.title                       as line_title,
                ol.price                       as price,
                ol.quantity,
                ol.fulfillment_status,
                o.currency,
                o.created_at::date             as created_at,
                o.name                         as order_no,
                o.shipping_address_country_code,
                o.shipping_address_province_code,
                o.shipping_address_latitude    as latitude,
                o.shipping_address_longitude   as longitude,
                o.processing_method,
                o.cancelled_at,
                o.closed_at,
                o.cancel_reason,
                o.confirmed,
                f.status                       as f_status,
                f.tracking_company,
                f.shipment_status,
                olr.quantity                   as refund_quantity,
                olr.subtotal                   as refund_subtotal,
                prod.title                     as product_name,
                trim(upper(prod.PRODUCT_TYPE)) as product_type,
                t.status                       as payment_status,
                pv.option_1,
                pv.option_2,
                pv.option_3,
                'AUS'                          as geo
         from fivetran_au_shopify.order_line as ol
                  left join unagi_edw.fivetran_au_shopify."ORDER" as o on o.id = ol.order_id
                  left join fivetran_au_shopify.fulfillment_order_line as fol on fol.order_line_id = ol.id
                  left join fivetran_au_shopify.order_line_refund as olr on olr.order_line_id = ol.id
                  left join fivetran_au_shopify.fulfillment as f on f.id = fol.fulfillment_id
                  left join fivetran_au_shopify.product as prod on prod.id = ol.product_id
                  left join fivetran_au_shopify.transaction as t on t.order_id = o.id
                  left join fivetran_au_shopify.product_variant as pv on pv.product_id = ol.variant_id
     ),
     ca_orders as (
/*
***** CANADIAN ORDERS *****
 */
         select ol.id                          as line_id,
                ol.name                        as line_desc,
                ol.title                       as line_title,
                ol.price                       as price,
                ol.quantity,
                ol.fulfillment_status,
                o.currency,
                o.created_at::date             as created_at,
                o.name                         as order_no,
                o.shipping_address_country_code,
                o.shipping_address_province_code,
                o.shipping_address_latitude    as latitude,
                o.shipping_address_longitude   as longitude,
                o.processing_method,
                o.cancelled_at,
                o.closed_at,
                o.cancel_reason,
                o.confirmed,
                f.status                       as f_status,
                f.tracking_company,
                f.shipment_status,
                olr.quantity                   as refund_quantity,
                olr.subtotal                   as refund_subtotal,
                prod.title                     as product_name,
                trim(upper(prod.PRODUCT_TYPE)) as product_type,
                t.status                       as payment_status,
                pv.option_1,
                pv.option_2,
                pv.option_3,
                'CAN'                          as geo
         from fivetran_ca_shopify.order_line as ol
                  left join unagi_edw.fivetran_ca_shopify."ORDER" as o on o.id = ol.order_id
                  left join fivetran_ca_shopify.fulfillment_order_line as fol on fol.order_line_id = ol.id
                  left join fivetran_ca_shopify.order_line_refund as olr on olr.order_line_id = ol.id
                  left join fivetran_ca_shopify.fulfillment as f on f.id = fol.fulfillment_id
                  left join fivetran_ca_shopify.product as prod on prod.id = ol.product_id
                  left join fivetran_ca_shopify.transaction as t on t.order_id = o.id
                  left join fivetran_ca_shopify.product_variant as pv on pv.product_id = ol.variant_id
     ),
     uk_orders as (
/*
***** CANADIAN ORDERS *****
 */
         select ol.id                          as line_id,
                ol.name                        as line_desc,
                ol.title                       as line_title,
                ol.price                       as price,
                ol.quantity,
                ol.fulfillment_status,
                o.currency,
                o.created_at::date             as created_at,
                o.name                         as order_no,
                o.shipping_address_country_code,
                o.shipping_address_province_code,
                o.shipping_address_latitude    as latitude,
                o.shipping_address_longitude   as longitude,
                o.processing_method,
                o.cancelled_at,
                o.closed_at,
                o.cancel_reason,
                o.confirmed,
                f.status                       as f_status,
                f.tracking_company,
                f.shipment_status,
                olr.quantity                   as refund_quantity,
                olr.subtotal                   as refund_subtotal,
                prod.title                     as product_name,
                trim(upper(prod.PRODUCT_TYPE)) as product_type,
                t.status                       as payment_status,
                pv.option_1,
                pv.option_2,
                pv.option_3,
                'UK'                           as geo
         from fivetran_uk_shopify.order_line as ol
                  left join unagi_edw.fivetran_uk_shopify."ORDER" as o on o.id = ol.order_id
                  left join fivetran_uk_shopify.fulfillment_order_line as fol on fol.order_line_id = ol.id
                  left join fivetran_uk_shopify.order_line_refund as olr on olr.order_line_id = ol.id
                  left join fivetran_uk_shopify.fulfillment as f on f.id = fol.fulfillment_id
                  left join fivetran_uk_shopify.product as prod on prod.id = ol.product_id
                  left join fivetran_uk_shopify.transaction as t on t.order_id = o.id
                  left join fivetran_uk_shopify.product_variant as pv on pv.product_id = ol.variant_id
     ),
     orders as (
         SELECT *
         FROM us_orders
         union all
         select *
         from eu_orders
         union all
         select *
         from au_orders
         union all
         select *
         from ca_orders
         union all
         select *
         from uk_orders
     ),
     time_periods as (
         select 'L24H'                              as period,
                dateadd('day', -1, sysdate())::date as start_at,
                sysdate()::date                     as end_at,
                1                                   as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'WTD'                                                                 as period,
                date_trunc('week', sysdate())::date                                   as start_at,
                sysdate()::date                                                       as end_at,
                datediff('day', date_trunc('week', sysdate())::date, sysdate()::date) as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'MTD'                                                                  as period,
                date_trunc('month', sysdate())::date                                   as start_at,
                sysdate()::date                                                        as end_at,
                datediff('day', date_trunc('month', sysdate())::date, sysdate()::date) as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'QTD'                                                                    as period,
                date_trunc('quarter', sysdate())::date                                   as start_at,
                sysdate()::date                                                          as end_at,
                datediff('day', date_trunc('quarter', sysdate())::date, sysdate()::date) as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'YTD'                                                                 as period,
                date_trunc('year', sysdate())::date                                   as start_at,
                sysdate()::date                                                       as end_at,
                datediff('day', date_trunc('year', sysdate())::date, sysdate()::date) as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         -- Previous Periods
         select 'PL24H'                             as period,
                dateadd('day', -2, sysdate())::date as start_at,
                dateadd('day', -1, sysdate())::date as end_at,
                1                                   as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'LWTD'                                                   as period,
                date_trunc('week', dateadd('week', -1, sysdate()))::date as start_at,
                dateadd('week', -1, sysdate())::date                     as end_at,
                datediff('day', date_trunc('week', dateadd('week', -1, sysdate()))::date,
                         dateadd('week', -1, sysdate())::date)           as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'LMTD'                                                     as period,
                date_trunc('month', dateadd('month', -1, sysdate()))::date as start_at,
                dateadd('month', -1, sysdate())::date                      as end_at,
                datediff('day', date_trunc('month', dateadd('month', -1, sysdate())::date),
                         dateadd('month', -1, sysdate())::date)            as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'LQTD'                                                         as period,
                date_trunc('quarter', dateadd('quarter', -1, sysdate()))::date as start_at,
                dateadd('quarter', -1, sysdate())::date                        as end_at,
                datediff('day', date_trunc('quarter', dateadd('quarter', -1, sysdate())::date)::date,
                         dateadd('quarter', -1, sysdate())::date)              as days_into_period
         from days
         where action_date::date = sysdate()::date
         union all
         select 'LYTD'                                                   as period,
                date_trunc('year', dateadd('year', -1, sysdate()))::date as start_at,
                dateadd('year', -1, sysdate())::date                     as end_at,
                datediff('day', date_trunc('year', dateadd('year', -1, sysdate())::date)::date,
                         dateadd('year', -1, sysdate())::date)           as days_into_period
         from days
         where action_date::date = sysdate()::date
     )
select time_periods.period,
       time_periods.start_at,
       time_periods.end_at,
       time_periods.days_into_period,
       sum(s."Total Subs") as "Total Subs",
       sum(s."Google Subs") as "Google Subs",
       sum(o."Total DTC") as "Total DTC",
       sum(o."USA DTC") as "USA DTC",
       sum(o."AUS DTC") AS "AUS DTC",
       sum(o."EUR DTC") AS "EUR DTC",
       sum(o."FR DTC") AS "FR DTC",
       sum(o."CAN DTC") AS "CAN DTC",
       sum(o."UK DTC") AS "UK DTC"
from time_periods
         left join (
    select p.period,
           sum(QUANTITY)                                                                            as "Total DTC",
           sum(IFF(geo = 'USA', QUANTITY, 0))                                                       as "USA DTC",
           sum(IFF(geo = 'AUS', QUANTITY, 0))                                                       as "AUS DTC",
           sum(IFF(trim(upper(SHIPPING_ADDRESS_COUNTRY_CODE)) <> 'FR' and geo = 'EU', QUANTITY, 0)) as "EUR DTC",
           sum(IFF(trim(upper(SHIPPING_ADDRESS_COUNTRY_CODE)) = 'FR' and geo = 'EU', QUANTITY, 0))  as "FR DTC",
           sum(IFF(geo = 'CAN', QUANTITY, 0))                                                       as "CAN DTC",
           sum(IFF(geo = 'UK', QUANTITY, 0))                                                        as "UK DTC"
    from orders
             left join time_periods as p on orders.created_at between p.start_at and p.end_at
    where FULFILLMENT_STATUS = 'fulfilled'
      and product_type = 'SCOOTER'
    group by 1
) as o on o.period = time_periods.period
    -- join subscribers
         left join (
    select p.period,
           count(distinct IFF(BILLING_REASON = 'subscription_create', statuses.sub_id, null)) as "Total Subs",
           count(distinct IFF(BILLING_REASON = 'subscription_create' and partner like '%google%', statuses.sub_id,
                              null))                                                          as "Google Subs"
    from statuses
             left join time_periods as p on statuses.action_date between p.start_at and p.end_at
        -- 3x nest join to find current day status
             left join (
        select statuses.sub_id,
               day_status
        from statuses
            -- find max. date for subscriber
                 left join (
            select distinct sub_id,
                            max(action_date) over (partition by sub_id) as max_date
            from statuses) as md
                           on md.sub_id = statuses.sub_id
        where case
                  when md.max_date > sysdate()::date
                      then action_date = sysdate()::DATE
                  else md.max_date = action_date
                  end
    ) as most_recent on statuses.sub_id = most_recent.sub_id
    where key = true
      and most_recent.day_status not in ('voided')
    group by 1
) as s on s.period = time_periods.period

group by 1,2,3,4
order by 1 desc
-- select * from time_periods
-- left join (select * from statuses where BILLING_REASON = 'subscription_create' and key=true) as s on s.action_date::date between time_periods.start_at and time_periods.end_at
/**
  logic for most recent status day
  iif(
    { FIXED [SUB_ID]: MAX([ACTION_DATE])} > TODAY(),
    DATETRUNC('day',[ACTION_DATE]) = DATETRUNC('day', TODAY()) and [MOST_RECENT_INVOICE] = TRUE
, { FIXED [SUB_ID]: MAX([ACTION_DATE])} = [ACTION_DATE] and [MOST_RECENT_INVOICE] = TRUE

  if
    max action_date for sub > today,
    action_date = today (dtrunc both) and most_recent_invoice = true
    else max action date for sub = this action_date and most_recent_invoice = true
)


 */