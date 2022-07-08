import os
ps_registry = [
    {
        "id": "daily_sales",
        "file": 'daily_sales.sql',
        "connection": "snowflake"
    },
    {
        "id": "all_customers",
        "file": 'all_customers.sql',
        "connection": "snowflake"
    },
    {
        "id": "sub_current_slot",
        "file": 'sub_current_slot.sql',
        "connection": "postgres"
    }

]


def find_prepared_statement(id: str, append: {}):
    # TODO: path routing not working with .ini file base directory in production, manually have to remove src/
    # add src/services/sql_files if development
    PREPARED_STATEMENT_BASE = 'services/sql_files/'
    for pid in ps_registry:
        if id == pid['id']:
            path = os.path.abspath(PREPARED_STATEMENT_BASE + '/' + pid['file'])
            query = open(path)
            query = query.read()
            if id == 'sub_current_slot':
                phone, email = 9999999999999999999, 9999999999999999999
                if 'phone' in append.keys():
                    phone = append['phone']
                if 'email' in append.keys():
                    email = append['email']
                query += f""" where email = '{email}' or phone = '{phone}'"""
            return {"query": query, "connection": pid['connection']}
    return None
