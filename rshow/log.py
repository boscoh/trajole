import logging


def init_logging():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("root").setLevel(logging.WARNING)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.INFO)
