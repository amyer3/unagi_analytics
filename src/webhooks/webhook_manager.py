"""
This file is the entrypoint to all webhooks.
Use it to search for and execute all webhooks based on parameters provided to search_and_execute function
FUNCTION IS WRAPPED IN THREAD IN OUTER SCOPE WHEN CALLED
"""
from zendesk_new_ticket.WEBHOOK_zendesk_new_ticket import search_and_update


def search_and_execute(service: str, action: str, data: str, connection):
    pass