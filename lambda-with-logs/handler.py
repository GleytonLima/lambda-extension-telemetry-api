import socket
import logging

from log_formatter_json_example import FormatterJSON
logger = logging.getLogger()
logger.setLevel('INFO')

formatter = FormatterJSON(
    '[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n',
    '%Y-%m-%dT%H:%M:%S'
)

# Replace the LambdaLoggerHandler formatter:
logger.handlers[0].setFormatter(formatter)


def handle(event, context):
    logger.info('Evento recebido', extra=dict(data=event))
    return {
        'statusCode': 200,
        'body': {
            'message': 'Hello from ' + socket.gethostname()
        }
    }
