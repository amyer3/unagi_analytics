def get_all_customers(phone:str, email: str, connection:{}):
    query = f"select * from all_customers where (email = '{email}' or PHONE::text like '%{phone}')"
    return connection.get_data('snowflake', query)