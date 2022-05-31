import json, sys, os
import snowflake.connector as snowflake_connector
import psycopg2 as psycopg2
#https://github.com/eabglobal/juniper
"""
provide layer to connect to UNAGI databases, perform queries
"""
get_geos = """
        SELECT 
            distinct id, 
            gp.n_times,
            gp.n_success
        from locations as l
        left join (
            select 
                location_id, 
                count(*) filter ( where is_successful = true ) as n_success, 
                count(*) as n_times 
            from geo_points group by 1) as gp on gp.location_id = l.id
        """
get_slots = "SELECT * FROM slot"
sf_get_subs = """
        select 
            s.id,
            c.shipping_address_line_1,
            c.shipping_address_line_2,
            c.shipping_address_city,    
            c.shipping_address_state, 
            c.shipping_address_postal_code,
            c.shipping_address_country
        from UNAGI_EDW.FIVETRAN_STRIPE.SUBSCRIPTION as s
        left join UNAGI_EDW.FIVETRAN_STRIPE.CUSTOMER as c on c.id = s.customer_id
        """

schema = {
    "transactions": [
        {
            "connection": "postgres",
            "method": "get",
            "query": "SELECT * FROM slot",
            "columns": "todo"
        },
        {
            "connection": "snowflake",
            "method": "get",
            "query": "SELECT * FROM FIVETRAN_STRIPE.SUBSCRIPTION"
        }
    ]

}


class Connection:
    def __init__(self):
        self.cursors = {
            "postgres": self.pg_connect(),
            "snowflake": self.sf_connect()
        }
        self.query_history = []

    def route_method(self, method: str):
        pass

    def check_connection(self, connection: str):
        if connection not in self.cursors:
            raise Exception("Unknown connection identifier: %s passed to Connection.get_data(), options are: %s" % (
                connection, ', '.join(self.cursors.keys())))
        return

    def update_data(self, connection: str, query: str):
        self.check_connection(connection=connection)

    def get_data(self, connection: str, query: str):
        self.check_connection(connection=connection)

        c = self.cursors[connection]
        try:
            c.execute(query)
            results = c.fetchall()
            return results
        except Exception:
            pass

    def pg_connect(self):
        try:
            return psycopg2.connect(
                host="db-postgresql-sfo2-76942-do-user-8637590-0.b.db.ondigitalocean.com",
                dbname="defaultdb-pool",
                user="doadmin",
                password="kiutqfyoi3kiz1ce",
                port='25061',
                sslmode='require'
            ).cursor()
        except Exception:
            pass

    def sf_connect(self):
        try:
            return snowflake_connector.connect(
                user='RETOOL_USER',
                password='O9am8Aj(1ma*',
                account='mk25046.us-central1.gcp',
                warehouse='SEGMENT_WAREHOUSE',
                database='UNAGI_EDW'
            ).cursor()
        except Exception:
            pass


def lambda_handler(event, context):
    # pg_slots = pd.DataFrame(data=results, columns=['sub_id', 'successful'])
    # sf_subs = pd.DataFrame(data=sf_results,
    #                       columns=['sub_id', 'addr1', 'addr2', 'city', 'state', 'post_code', 'country'])
    #
    c = Connection()

    for txn in event['transactions']:
        txn['result'] = c.get_data(connection=txn['connection'], query=txn['query'])

    return event


def test():
    print(snowflake_connector)
    print(psycopg2)
    c = lambda_handler(schema, '')
    #print(c)
