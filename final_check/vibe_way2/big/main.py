import argparse
import datetime
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(1)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail(message.splitlines()[0])


def dec(value, label, allow_negative=False):
    try:
        d = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        fail(f"--{label} must be a number")
    if not d.is_finite():
        fail(f"--{label} must be a number")
    if d < 0 and not allow_negative:
        fail(f"--{label} must not be negative")
    return d


def money(d):
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(d):
    return "${:.2f}".format(d)


def main():
    p = Parser(description="Order batch helper")
    for name in ("customer", "email", "phone", "qty", "price",
                 "discount-percent", "tax-percent", "ship-date", "days-to-deliver"):
        p.add_argument("--" + name, required=True)
    a = p.parse_args()

    customer = a.customer.strip().title()
    if not customer:
        fail("customer must not be empty")

    email = a.email.strip().lower()
    if email.count("@") != 1:
        fail("email must contain exactly one @")
    local, domain = email.split("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        fail("email is not valid")

    phone = re.sub(r"\D", "", a.phone)
    if len(phone) != 10:
        fail("phone must have 10 digits")

    qty = dec(a.qty, "qty")
    price = dec(a.price, "price")
    disc_pct = dec(a.discount_percent, "discount-percent")
    tax_pct = dec(a.tax_percent, "tax-percent")
    if disc_pct > 100:
        fail("--discount-percent must be at most 100")

    try:
        ship = datetime.date.fromisoformat(a.ship_date.strip())
    except ValueError:
        fail("--ship-date must be YYYY-MM-DD")
    try:
        days = int(a.days_to_deliver.strip())
        delivery = ship + datetime.timedelta(days=days)
    except (ValueError, OverflowError):
        fail("--days-to-deliver must be a whole number of days")
    if days < 0:
        fail("--days-to-deliver must not be negative")

    subtotal = money(qty * price)
    discount = money(subtotal * disc_pct / 100)
    taxable = subtotal - discount
    tax = money(taxable * tax_pct / 100)
    total = taxable + tax

    print(json.dumps({
        "customer": customer,
        "email": email,
        "phone": phone,
        "subtotal": fmt(subtotal),
        "discount": fmt(discount),
        "tax": fmt(tax),
        "total": fmt(total),
        "delivery_date": delivery.isoformat(),
    }))


if __name__ == "__main__":
    main()
