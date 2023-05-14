import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# create handlers
log_info_handler = logging.FileHandler("logs/info.log")
log_info_handler.setLevel(logging.INFO)
log_debug_handler = logging.FileHandler("logs/debug.log")
log_debug_handler.setLevel(logging.DEBUG)

# create formatter
log_formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(funcName)s]{%(levelname)s} %(message)s')

# add formatter to handler
log_info_handler.setFormatter(log_formatter)
log_debug_handler.setFormatter(log_formatter)

# add handler to logger
log.addHandler(log_info_handler)
log.addHandler(log_debug_handler)

