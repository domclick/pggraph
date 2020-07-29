"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from argparse import ArgumentParser, Namespace
import logging
from logging import handlers
import os
from pprint import pprint

from pggraph.api import PgGraphApi
from pggraph.utils.action_enum import ActionEnum


def main():
    args = parse_args()
    setup_logging(args.log_level, args.log_path)

    pg_graph_api = PgGraphApi(config_path=args.config_path)
    result = pg_graph_api.run_action(args)

    pprint(result)


def setup_logging(log_level: str = 'INFO', log_path: str = None):
    log_handlers = [logging.StreamHandler()]
    if log_path:
        log_path = os.path.join(log_path, "pggraph.log")
        logging.handlers.RotatingFileHandler(log_path, maxBytes=1000000, backupCount=3, encoding="UTF-8")

    logging.basicConfig(handlers=log_handlers,
                        level=log_level or logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    logging.getLogger('psycopg2').setLevel(log_level)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "action",
        type=str,
        help=f"required action: {', '.join(ActionEnum.list_values())}",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="table name",
        required=True,
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="primary key ids, separated by comma, e.g. 1,2,3",
    )
    parser.add_argument(
        "--config_path",
        type=str,
        default='config.ini',
        help="path to config.ini",
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default=None,
        help="path to log dir",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default='info',
        help="log level (debug, info, error)",
    )
    args = parser.parse_args()

    args.action = ActionEnum[args.action]
    if args.ids:
        args.ids = [int(id_) for id_ in str(args.ids).split(',')]
    if args.log_level:
        args.log_level = str(args.log_level).upper()

    return args


if __name__ == "__main__":
    main()

