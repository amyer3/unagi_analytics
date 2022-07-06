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
    }

]


def find_prepared_statement(id: str):
    # TODO: path routing not working with .ini file base directory in production, manually have to remove src/
    PREPARED_STATEMENT_BASE = 'src/services/sql_files/'
    for pid in ps_registry:
        if id == pid['id']:
            path = os.path.abspath(PREPARED_STATEMENT_BASE +'/'+ pid['file'])
            query = open(path)
            query = query.read()
            return {"query": query, "connection": pid['connection']}
    return None
