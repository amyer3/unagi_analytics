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
    PREPARED_STATEMENT_BASE = '../prepareds_scripts/'
    for pid in ps_registry:
        if id == pid['id']:
            query = open(PREPARED_STATEMENT_BASE + pid['file'])
            query = query.read()
            return {"query": query, "connection": pid['connection']}
    return None
