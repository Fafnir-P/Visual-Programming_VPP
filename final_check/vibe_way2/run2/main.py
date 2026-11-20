#!/usr/bin/env python3
import argparse
import json
import sys


class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: " + message.splitlines()[0] + "\n")
        sys.exit(1)


def to_number(value, label):
    try:
        return float(value)
    except (TypeError, ValueError):
        sys.stderr.write(f"error: --{label} must be a number\n")
        sys.exit(1)


def main():
    parser = Parser(description="Order line helper")
    parser.add_argument("--customer", required=True)
    parser.add_argument("--qty", required=True)
    parser.add_argument("--price", required=True)
    args = parser.parse_args()

    customer = args.customer.strip().title()
    if not customer:
        sys.stderr.write("error: customer must not be empty\n")
        sys.exit(1)

    total = to_number(args.qty, "qty") * to_number(args.price, "price")
    print(json.dumps({"customer": customer, "total": "${:.2f}".format(total)}))


if __name__ == "__main__":
    main()
