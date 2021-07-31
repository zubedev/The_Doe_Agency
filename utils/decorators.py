import logging


def suppress_logs(original_function, loglevel="ERROR"):
    def new_function(*args, **kwargs):
        """wrap original_function with suppressed warnings"""
        # raise logging level to ERROR or loglevel
        logger = logging.getLogger("django")
        previous_logging_level = logger.getEffectiveLevel()
        logger.setLevel(getattr(logging, loglevel.upper()))

        # trigger original function that would throw warning
        original_function(*args, **kwargs)

        # lower logging level back to previous
        logger.setLevel(previous_logging_level)

    return new_function
