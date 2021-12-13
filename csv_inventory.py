#!/usr/bin/env python

import json
import os
import argparse
import configparser
import csv
import sys
import six

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

config_file = "csv_inventory.cfg"
default_group = "NO_GROUP"


def find_config_file():
    env_name = "CSV_INVENTORY_CONFIG"
    if env_name in os.environ:
        return os.environ[env_name]
    else:
        return config_file


def main():
    args = parse_args()
    if args.config:
        create_config(
            filename=args.file,
            group_by_col=args.group_by_col,
            hostname_col=args.hostname_col,
        )
    config_path = find_config_file()
    config = load_config(config_path)
    try:
        inventory = csv_to_inventory(
            file=config["csv_inventory_file"],
            group_by_col=config["group_by_col"],
            hostname_col=config["hostname_col"],
        )
        if args.list:
            print(json.dumps(inventory, indent=4, sort_keys=True, default=str))
        if args.config:
            create_config(
                filename=args.file,
                group_by_col=args.group_by_col,
                hostname_col=args.hostname_col,
            )
        elif args.host:
            try:
                print(
                    json.dumps(
                        inventory["_meta"]["hostvars"][args.host],
                        indent=4,
                        sort_keys=True,
                        default=str,
                    )
                )
            except KeyError as e:
                print('\033[91mHost "%s" not Found!\033[0m' % e)
                print(e)
    except FileNotFoundError as e:
        print(
            "\033[91mFile Not Found! Check %s configuration file!"
            " Is the `csv_inventory_file` path setting correct?\033[0m" % config_path
        )
        print(e)
        exit(1)
    exit(0)


def create_config(filename=None, group_by_col=None, hostname_col=None):
    config = configparser.ConfigParser()
    config["csv_inventory"] = {}
    config["csv_inventory"]["csv_inventory_file"] = filename
    if group_by_col is not None:
        config["csv_inventory"]["group_by_col"] = str(group_by_col)
    if hostname_col is not None:
        config["csv_inventory"]["hostname_col"] = str(hostname_col)
    with open(find_config_file(), "w") as cf:
        config.write(cf)


def load_config(config_path):
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"hostname_col": 1, "group_by_col": 2}
    if len(config.read(config_path)) > 0:
        return config["csv_inventory"]
    print('\033[91mConfiguration File "%s" not Found!\033[0m' % config_path)
    exit(1)


def parse_args():
    arg_parser = argparse.ArgumentParser(description="CSV Inventory Module")
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List active servers")
    group.add_argument(
        "--host", help="List details about the specified host", default=None
    )
    group.add_argument("--config", action="store_true", help="Create Config File")
    arg_parser.add_argument(
        "--file",
        required="--config" in sys.argv,
        help="CSV file used by csv_inventory.py",
    )
    arg_parser.add_argument(
        "--group-by-col", default=None, help="Column to group hosts by (i.E. `B`)"
    )
    arg_parser.add_argument(
        "--hostname-col",
        required="--config" in sys.argv,
        help="Column containing the hostnames",
    )
    return arg_parser.parse_args()


def csv_to_inventory(file, group_by_col, hostname_col):
    groups = {"_meta": {"hostvars": {}}}
    with open(file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            host = row[hostname_col]
            if host is None:
                continue
            group = row[group_by_col] if group_by_col in row else default_group
            if group not in groups:
                groups[group] = {"hosts": [], "vars": {}}
            groups[group]["hosts"].append(host)
            groups["_meta"]["hostvars"][row[hostname_col]] = {
                k.replace(" ", "_"): v for k, v in row.items()
            }
    return groups


if __name__ == "__main__":
    main()
