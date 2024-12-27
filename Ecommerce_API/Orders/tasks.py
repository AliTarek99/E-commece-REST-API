from celery import shared_task
from orders.models import Orders
from orders.services import OrdersServices
from users.models import CustomUser


@shared_task
def update_pending_order(order_id, user_id):
    print('in task', order_id, user_id)
    order = Orders.objects.filter(id=order_id).first()
    if not order or order.status != Orders.PENDING:
        return
    order.status = Orders.FAILED
    order.save()
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return
    OrdersServices.restore_items(order, user)