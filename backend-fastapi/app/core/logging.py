from loguru import logger
logger.add('logs/app.log', rotation='10 MB', retention='7 days', enqueue=True)
