import json
import pika
import os

from datetime import datetime


def send_slack_message(channel: str, msg: str, **kwargs) -> None:
    """Отправляет сообщение в  slack.

    :param channel: канал, на который будет отправлено сообщение.
    :param msg: текст сообщения.
    :param kwargs: другие параметры сообщения, такие как  title, pretext, color, url.
    """

    data = {'channel': channel, 'text': msg}
    data.update(kwargs)

    try:
        credentials = pika.PlainCredentials(
            os.environ.get("RMQ_USER", os.getcwd()), os.environ.get("RMQ_PASS", os.getcwd()))
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(os.environ.get("RMQ_HOST", os.getcwd()), os.environ.get("RMQ_PORT", os.getcwd()), 'slack', credentials))
        channel = connection.channel()
        channel.queue_declare(queue='send', durable=False)

        channel.basic_publish(
            exchange='', routing_key='send', body=json.dumps(data))

        connection.close()
        write_logs(f'Slack message was sent: {data}')
    except pika.exceptions.AMQPConnectionError as error:
        write_logs(error)
    except pika.exceptions.UnroutableError as error:
        write_logs(error)


def write_logs(message):
    # Get the logs path from environment, default to the current working directory
    logs_path = os.environ.get("LOGS_PATH", os.getcwd())

    # Create run_logs directory if it doesn't exist within the specified logs path
    logs_directory = os.path.join(logs_path, "run_logs")
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    print("Writing to logs directory:", logs_directory)

    # Generate a unique filename using the current timestamp within the logs directory
    filename = datetime.now().strftime(f"{logs_directory}/slack_logging_%Y%m%d_%H%M%S.json")

    # Write the messages dict into a new file for each run
    with open(filename, "w") as f:
        f.write(message)