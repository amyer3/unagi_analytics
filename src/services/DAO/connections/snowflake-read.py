from ..Connection import Connection


class SnowflakeRead(Connection):
    def __init__(self, **kwargs):
        super().__init__(
            name='Snowflake Read Only Connection',
            database='snowflake',
            connectionObject={
                "user": 'RETOOL_USER',
                'password': 'O9am8Aj(1ma*',
                'account': 'mk25046.us-central1.gcp',
                'warehouse': 'SEGMENT_WAREHOUSE',
                'database': 'UNAGI_EDW'
            }
        )