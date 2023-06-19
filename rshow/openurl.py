import logging
import threading
import time
import webbrowser
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def open_url_in_background(test_url, open_url=None, sleep_in_s=1):
    """
    Polls server in background thread then opens a url in webbrowser
    """
    if open_url is None:
        open_url = test_url

    def inner():
        elapsed = 0
        while True:
            try:
                response_code = urlopen(test_url).getcode()
                if response_code < 400:
                    logger.info(f"open_url_in_background open {open_url}")
                    webbrowser.open(open_url)
                    return
            except:
                time.sleep(sleep_in_s)
                elapsed += sleep_in_s
                logger.info(f"testing {test_url} waiting {elapsed}s")

    # creates a thread to poll server before opening client
    logger.debug(f"open_url_in_background testing {test_url} to open {open_url}")
    threading.Thread(target=inner).start()
