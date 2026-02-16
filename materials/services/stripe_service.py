import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_product(name, description=""):
    """Создаёт продукт в Stripe"""
    return stripe.Product.create(name=name, description=description)


def create_stripe_price(product_id, amount):
    """Создаёт цену (в копейках!)"""
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount * 100,  # рубли → копейки
        currency="rub"
    )


def create_stripe_checkout_session(price_id, success_url, cancel_url):
    """Создаёт сессию оплаты"""
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session