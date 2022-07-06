--SET tda = sysdate()::date;
WITH
  days          AS (
	SELECT
	  SEQ4()                                                               AS idx,
	  DATEADD(DAY, SEQ4(), '2020-08-01 00:00:00 +000'::timestamp_tz)::date AS action_date
	FROM TABLE (GENERATOR(ROWCOUNT => 5000)) AS v
  ),
  statuses      AS (select * from WW_SUB_DAILY_STATUS),-- end of cte
  scooters_sold AS (
	SELECT *
	FROM WW_DTC_LINE_ITEMS
	WHERE TOTAL_DISCOUNT < price
	  AND order_total > 0
	  AND FULFILLMENT_STATUS = 'fulfilled'
	  AND COALESCE(refund_quantity, 0) < QUANTITY
	  AND payment_status = 'paid'
	  AND product_type = 'SCOOTER'
  ),
  time_periods  AS (
	SELECT
	  'L24H'                              AS period,
	  DATEADD('day', -1, SYSDATE()::date) AS start_at,
	  DATEADD('day', -1, SYSDATE()::date) AS end_at,
	  1                                   AS days_into_period,
	  1                                   AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	SELECT
	  'WTD'                                                                       AS period,
	  DATE_TRUNC('week', SYSDATE()::date)                                         AS start_at,
	  DATEADD('day', -1, DATE_TRUNC('week', DATEADD('week', 1, SYSDATE())))::date AS end_at,
	  DATEDIFF('day', DATE_TRUNC('week', SYSDATE()::date), SYSDATE()::date)       AS days_into_period,
	  DATEDIFF('day', DATE_TRUNC('week', SYSDATE()::date),
			   DATE_TRUNC('week', DATEADD('week', 1, SYSDATE()::date)))           AS t_days_in_period
	FROM days
	WHERE action_date= SYSDATE()::date
	UNION ALL
	SELECT
	  'MTD'                                                                         AS period,
	  DATE_TRUNC('month', SYSDATE()::date)                                          AS start_at,
	  DATEADD('day', -1, DATE_TRUNC('month', DATEADD('month', 1, SYSDATE())))::date AS end_at,
	  DATEDIFF('day', DATE_TRUNC('month', SYSDATE()::date), SYSDATE()::date)        AS days_into_period,
	  DATEDIFF('day', DATE_TRUNC('month', SYSDATE()::date),
			   DATE_TRUNC('month', DATEADD('month', 1, SYSDATE()::date)))           AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	SELECT
	  'QTD'                                                                             AS period,
	  DATE_TRUNC('quarter', SYSDATE()::date)                                            AS start_at,
	  DATEADD('day', -1, DATE_TRUNC('quarter', DATEADD('quarter', 1, SYSDATE())))::date AS end_at,
	  DATEDIFF('day', DATE_TRUNC('quarter', SYSDATE()::date), SYSDATE()::date)          AS days_into_period,
	  DATEDIFF('day', DATE_TRUNC('quarter', SYSDATE()::date),
			   DATE_TRUNC('quarter', DATEADD('quarter', 1, SYSDATE()::date)))           AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	SELECT
	  'YTD'                                                                       AS period,
	  DATE_TRUNC('year', SYSDATE()::date)                                         AS start_at,
	  DATEADD('day', -1, DATE_TRUNC('year', DATEADD('year', 1, SYSDATE())))::date AS end_at,
	  DATEDIFF('day', DATE_TRUNC('year', SYSDATE()::date), SYSDATE()::date)       AS days_into_period,
	  DATEDIFF('day', DATE_TRUNC('year', SYSDATE()::date),
			   DATE_TRUNC('year', DATEADD('year', 1, SYSDATE()::date)))           AS t_days_in_period

	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	-- Previous Periods
	/**
	  today 1 year ago
	 */
	SELECT
	  'PL24H'                                                  AS period,
	  DATEADD('year', -1, DATEADD('day', -1, SYSDATE()::date)) AS start_at,
	  DATEADD('year', -1, DATEADD('day', -1, SYSDATE()::date)) AS end_at,
	  1                                                        AS days_into_period,
	  1                                                        AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	/**
	  This WTD Last year
	 */
	SELECT
	  'LWTD'                                                   AS period,
	  DATEADD('year', -1, DATE_TRUNC('week', SYSDATE()::date)) AS start_at,
	  DATEADD('year', -1, SYSDATE()::date)                     AS end_at,
	  DATEDIFF('day', DATE_TRUNC('week', DATEADD('week', -1, SYSDATE()::date)),
			   DATEADD('week', -1, SYSDATE()::date))           AS days_into_period,
	  7                                                        AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL

	/**
	  this MTD last year
	 */
	SELECT
	  'LMTD'                                                    AS period,
	  DATE_TRUNC('month', DATEADD('year', -1, SYSDATE()::date)) AS start_at,
	  DATEADD('year', -1, SYSDATE()::date)                      AS end_at,
	  DATEDIFF('day', DATE_TRUNC('month', DATEADD('month', -1, SYSDATE()::date)),
			   DATEADD('month', -1, SYSDATE()::date))           AS days_into_period,
	  30                                                        AS t_days_in_period

	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	/**
	  This quarter last year
	 */
	SELECT
	  'LQTD'                                                      AS period,
	  DATE_TRUNC('quarter', DATEADD('year', -1, SYSDATE()::date)) AS start_at,
	  DATEADD('year', -1, SYSDATE()::date)                        AS end_at,
	  DATEDIFF('day', DATE_TRUNC('quarter', DATEADD('quarter', -1, SYSDATE()::date)),
			   DATEADD('quarter', -1, SYSDATE()::date))           AS days_into_period,
	  91                                                          AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
	UNION ALL
	/**
	  this YTD last year
	 */
	SELECT
	  'LYTD'                                                   AS period,
	  DATE_TRUNC('year', DATEADD('year', -1, SYSDATE()::date)) AS start_at,
	  DATEADD('year', -1, SYSDATE()::date)                     AS end_at,
	  DATEDIFF('day', DATE_TRUNC('year', DATEADD('year', -1, SYSDATE()::date)),
			   DATEADD('year', -1, SYSDATE()::date))           AS days_into_period,
	  365                                                      AS t_days_in_period
	FROM days
	WHERE action_date = SYSDATE()::date
  )
SELECT
  time_periods.period,
  time_periods.start_at,
  time_periods.end_at,
  time_periods.days_into_period,
  time_periods.t_days_in_period,
  -- Flat forecast the subscription numbers
  -- put days into period into 1 indexed, will err at 0 index as div/0
  COALESCE(
	ROUND((SUM(s."Total Subs") / (days_into_period+1)) * IFF(time_periods.period LIKE '%24H', 2, t_days_in_period),
		  0), 0)                    AS "Sub Forecast",
  COALESCE(ROUND((SUM(o."Total DTC") / (days_into_period+1)) *
				 IFF(time_periods.period LIKE '%24H', 2, t_days_in_period),
				 0), 0)             AS "DTC Forecast",
  COALESCE(SUM(s."Total Subs"), 0)  AS "Total Subs",
  COALESCE(SUM(s."Google Subs"), 0) AS "Google Subs",
  COALESCE(SUM(o."Total DTC"), 0)   AS "Total DTC",
  COALESCE(SUM(o."USA DTC"), 0)     AS "USA DTC",
  COALESCE(SUM(o."AUS DTC"), 0)     AS "AUS DTC",
  COALESCE(SUM(o."EUR DTC"), 0)     AS "EUR DTC",
  COALESCE(SUM(o."FR DTC"), 0)      AS "FR DTC",
  COALESCE(SUM(o."CAN DTC"), 0)     AS "CAN DTC",
  COALESCE(SUM(o."UK DTC"), 0)      AS "UK DTC"
FROM time_periods
  LEFT JOIN (
			  SELECT
				p.period,
				SUM(QUANTITY)                                                                            AS "Total DTC",
				SUM(IFF(geo = 'USA', QUANTITY, 0))                                                       AS "USA DTC",
				SUM(IFF(geo = 'AUS', QUANTITY, 0))                                                       AS "AUS DTC",
				SUM(IFF(UPPER(TRIM(SHIPPING_ADDRESS_COUNTRY_CODE)) <> 'FR' AND geo = 'EU', QUANTITY, 0)) AS "EUR DTC",
				SUM(IFF(UPPER(TRIM(SHIPPING_ADDRESS_COUNTRY_CODE)) = 'FR' AND geo = 'EU', QUANTITY, 0))  AS "FR DTC",
				SUM(IFF(geo = 'CAN', QUANTITY, 0))                                                       AS "CAN DTC",
				SUM(IFF(geo = 'UK', QUANTITY, 0))                                                        AS "UK DTC"
			  FROM scooters_sold       AS orders
				LEFT JOIN time_periods AS p ON orders.created_at::date BETWEEN p.start_at AND p.end_at
				-- filtering done at scooters sold CTE
			  GROUP BY 1
			) AS o ON o.period = time_periods.period
			  -- join subscribers
  LEFT JOIN (
			  SELECT
				p.period,
				COUNT(DISTINCT statuses.sub_id)                            AS "Total Subs",
				COUNT(DISTINCT
					  IFF(partner LIKE '%google%', statuses.sub_id, NULL)) AS "Google Subs"
			  FROM statuses
				-- TODO: case when 24H, join on just the day only
				LEFT JOIN time_periods AS p ON
				IFF(p.period LIKE '%24%', statuses.subscription_start = p.start_at,
					statuses.subscription_start BETWEEN p.start_at AND p.end_at)
			  WHERE MOST_RECENT_STATUS not in ('voided', 'early cancel')

			  GROUP BY 1
			) AS s ON s.period = time_periods.period
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1 DESC