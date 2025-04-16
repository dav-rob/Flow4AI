from .. import jc_logging as logging


def printh(text):
    """
    Log the given text surrounded by asterisks.
    """
    logger = logging.getLogger('PrintUtils')
    logger.info("*** " + text + " ***")
