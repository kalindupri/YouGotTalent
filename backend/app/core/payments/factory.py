from functools import lru_cache

from app.core.config import settings
from app.core.payments.base import PaymentGateway
from app.core.payments.mock import MockGateway


@lru_cache
def get_gateway() -> PaymentGateway:
    if settings.PAYMENT_GATEWAY == "payhere":
        from app.core.payments.payhere import PayHereGateway

        return PayHereGateway()
    if settings.PAYMENT_GATEWAY == "stripe":
        from app.core.payments.stripe_gateway import StripeGateway

        return StripeGateway()
    return MockGateway()
