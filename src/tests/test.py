import base64
# test search_and_update
from ..webhooks.zendesk_new_ticket.WEBHOOK_zendesk_new_ticket import search_and_update
from ..services.connection_manager import Connection
c=Connection()
# search_and_update(ticket_id=86221, phone='4087053642', email='kyle@unagiscooters.com')
