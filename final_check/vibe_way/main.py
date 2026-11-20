import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def to_number(name, text):
    try:
        value = Decimal(text)
    except InvalidOperation:
        fail(f"{name} must be a number, got {text!r}")
    if not value.is_finite():
        fail(f"{name} must be a finite number, got {text!r}")
    return value


def main():
    parser = argparse.ArgumentParser(description="Order line helper")
    parser.add_argument("--customer", required=True)
    parser.add_argument("--qty", required=True)
    parser.add_argument("--price", required=True)
    try:
        args = parser.parse_args()
    except SystemExit as e:
        sys.exit(1 if e.code else 0)

    name = args.customer.strip().title()
    if not name:
        fail("customer name is empty")
    qty = to_number("qty", args.qty)
    price = to_number("price", args.price)
    total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    print(json.dumps({"customer": name, "total": f"${total:,.2f}".replace(",", "")}))


if __name__ == "__main__":
    main()
