import psycopg2
import snowflake.connector as snowflake_connector


class Connection:
    def __init__(self):
        self.cursors = {
            "postgres": self.pg_connect(),
            "snowflake": self.sf_connect(),
            "snowflake_write": self.sf_connect_write()
        }
        self.query_history = []

    def route_method(self, method: str):
        pass

    def check_connection(self, connection: str):
        if connection not in self.cursors:
            raise Exception("Unknown connection identifier: %s passed to Connection.get_data(), options are: %s" % (
                connection, ', '.join(self.cursors.keys())))
        c = self.cursors[connection]
        try:
            c.execute("SELECT 1")
            c.fetchall()
        except Exception as e:
            print(f"Received error checking connection {connection}: {e}")
            if connection == 'postgres':
                self.cursors[connection] = self.pg_connect()
            if connection == 'snowflake':
                self.cursors[connection] = self.sf_connect()
            if connection == 'snowflake_write':
                self.cursors[connection] = self.sf_connect_write()
        return

    def get_data(self, connection: str, query: str, return_mapped: bool = False):
        self.check_connection(connection=connection)
        c = self.cursors[connection]
        try:
            c.execute(query)
            results = c.fetchall()
            col_names = []
            for elt in c.description:
                col_names.append(elt[0])
            if return_mapped:
                return self._return_as_column_map(results, col_names)
            return {"data": results, "columns": col_names}
        except Exception as e:
            print(str(e))
            return {}

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

    def sf_connect_write(self):
        try:
            return snowflake_connector.connect(
                user='alex',
                password='O@lIGFq*gJErZmT8GUnVmJ4CqUtZI3xPqO8z!8VHcaxn&S8l^o^$ibU7',
                account='mk25046.us-central1.gcp',
                warehouse='SEGMENT_WAREHOUSE',
                database='UNAGI_EDW'
            ).cursor()
        except Exception:
            pass

    def _return_as_column_map(self, data: [[any]], columns: [str]) -> [{any}]:
        r = []
        for v in data:
            t = {}
            for i, k in enumerate(v):
                t[columns[i]] = k
            r.append(t)
        return r

