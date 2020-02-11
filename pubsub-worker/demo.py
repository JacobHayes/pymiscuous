""" Dummy worker.
"""
import json
import random
import time
import warnings
from typing import Optional

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

import pubsub_worker

PROJECT = "<your project>"
if PROJECT == "<your project>":
    raise ValueError("Set the PROJECT variable!")

# Set your project below.
TOPIC, SUBSCRIPTION = (
    f"projects/{PROJECT}/topics/dummy",
    f"projects/{PROJECT}/subscriptions/dummy-worker",
)

# Ignore Google Cloud cred warnings when working locally.
warnings.filterwarnings(
    "ignore", "Your application has authenticated using end user credentials"
)


def publish_message(publisher, sleep, msg=None):
    pubsub_message = {"sleep": sleep}
    if msg is not None:
        pubsub_message["msg"] = msg
    publisher.publish(TOPIC, json.dumps(pubsub_message).encode())


def bootstrap_queue(publisher, subscriber):
    """ Create the topic+subscription if they do not exist and add some dummy messages.

        Normally messages would be published in a separate process/worker (though a
        worker may submit to a different queue as part of it's work).
    """
    try:
        publisher.create_topic(TOPIC)
    except AlreadyExists:
        pass
    try:
        subscriber.create_subscription(SUBSCRIPTION, TOPIC)
    except AlreadyExists:
        pass
    # Publish a helper message and some dummy work. Publish must happen after the
    # subscription is made.
    helper_msg = (
        "Hit Ctrl-C to gracefully stop the worker at any time - it will wait for any "
        "in-progress jobs to finish!"
    )
    publish_message(publisher, sleep=0, msg=helper_msg)
    for _ in range(500):
        publish_message(publisher, sleep=random.randint(1, 10))
    print(f"Published some dummy messages!")


def demo():
    """ Run the demo!
    """
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    bootstrap_queue(publisher, subscriber)

    def echo(sleep: int, msg: Optional[str] = None):
        """ Do lots of work.
        """
        time.sleep(sleep)
        if msg is None:
            msg = f"Completed sleeping {sleep} seconds!"
        print(msg)
        # Wouldn't usually publish to the same queue, but let's keep the demo alive (but
        # slowly stopping)!
        if random.choice([True, False, False, False]):
            print("Adding another task for fun...")
            publish_message(publisher, sleep=random.randint(1, 5))

    pubsub_worker.PubSubWorker(subscriber).run(SUBSCRIPTION, echo)


if __name__ == "__main__":
    demo()
