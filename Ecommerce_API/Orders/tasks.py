from celery import shared_task
from orders.models import Orders
from orders.services import OrdersServices
from users.models import CustomUser
import constants


@shared_task
def update_pending_order(order_id, user_id):
    print('in task', order_id, user_id)
    order = Orders.objects.filter(id=order_id).first()
    if not order or order.status != constants.ORDER_PENDING:
        return
    order.status = constants.ORDER_FAILED
    order.save()
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return
    OrdersServices.restore_items(order, user)