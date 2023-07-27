import logging


def init_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(name)s:%(funcName)s: %(message)s"
    )
    logging.getLogger("root").setLevel(logging.WARNING)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.INFO)
