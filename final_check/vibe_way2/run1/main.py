import argparse
import json
import sys


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def num(text, name):
    try:
        return float(text)
    except ValueError:
        fail(f"error: {name} must be a number")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--customer", required=True)
    p.add_argument("--qty", required=True)
    p.add_argument("--price", required=True)
    try:
        a = p.parse_args()
    except SystemExit:
        sys.exit(1)
    name = a.customer.strip().title()
    if not name:
        fail("error: customer name is empty")
    total = num(a.qty, "qty") * num(a.price, "price")
    print(json.dumps({"customer": name, "total": f"${total:.2f}"}))


if __name__ == "__main__":
    main()
