def get_subscription_orders(customer_ids: [str], connection: {}) -> [[{any}], [str]]:
    # get all subscription records for this customer
    # THEN, clean the array to pull all slot records for each subscription ID
    # THEN clean and pull most recent INBOUND and OUTBOUND records for each slot
    customer_id_string = ','.join("'%s'" % i for i in customer_ids)
    sub_query = f"""select s.id, s.start_date, s.ended_at, d.most_recent_status as status, d.partner from fivetran_stripe.subscription s
         inner join FIVETRAN_STRIPE.SUB_DAILY d on s.id = d.SUB_ID and d._KEY = true 
         where s.CUSTOMER_ID in ({customer_id_string})"""
    sub_orders = connection.get_data("snowflake", query=sub_query)
    return [sub_orders['data'],
            sub_orders['columns']]