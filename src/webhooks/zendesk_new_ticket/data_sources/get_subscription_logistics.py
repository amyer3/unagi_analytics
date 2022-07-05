def get_subscription_logistics(subscription_ids: [str], connection: {}) -> any:
    sub_id_string = ','.join("'%s'" % i for i in subscription_ids)
    logi_query = f"""with inbound as ( select
					   l.created_at,
					   l.completed_at,
					   coalesce(l.tracking_number, l.onfleet_id) as tracking,
					   l.order_id                                as slot_id,
					   l.product_id,
					   l.status,
					   l.logistic_method,
					   l.direction
				from logistics l
				where l.status <> 'void' and (l.void_reason is null or l.void_reason ='') and l.product_type = 'scooter' and direction like '%inbound%'),
   outbound as ( select
					   l.created_at,
					   l.completed_at,
					   coalesce(l.tracking_number, l.onfleet_id) as tracking,
					   l.order_id                                as slot_id,
					   l.product_id,
					   l.status,
					   l.logistic_method,
					   l.direction
				from logistics l
				where l.status <> 'void' and (l.void_reason is null or l.void_reason ='') and l.product_type = 'scooter' and direction like '%outbound%')
select
  distinct s.id as slot_id,
  s.index,
  s.sub_id,
  s.status as status,
  o.product_id as product_id,
  s.start_type as sub_update_type,
  o.created_at as outbound_created_at,
  o.completed_at as outbound_completed_at,
  coalesce(o.tracking, '') as outbound_tracking,
  coalesce(o.logistic_method, '') as outbound_logistic,
  i.created_at as inbound_created_at,
  i.completed_at as inbound_completed_at,
  i.tracking as inbound_tracking,
  i.logistic_method as inbound_logistic
from slot s
left join outbound o on s.id = o.slot_id
left join inbound i on i.slot_id = o.slot_id
 where s.status <> 'void' and s.sub_id in ({sub_id_string})"""
    logi = connection.get_data('postgres', logi_query)
    return [logi['data'],
            logi['columns']]