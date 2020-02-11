""" Dummy worker.
"""
import json
import random
import time
import warnings

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

import worker

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
    publisher.publish(TOPIC, json.dumps({"sleep": "0", "msg": helper_msg}).encode())
    for _ in range(500):
        publisher.publish(TOPIC, json.dumps({"sleep": random.randint(1, 10)}).encode())
    print(f"Published some dummy messages!")


def demo():
    """ Run the demo!
    """
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    bootstrap_queue(publisher, subscriber)

    def echo(sleep: str, msg: str = None):
        """ Do lots of work.
        """
        sleep = int(sleep)
        if msg is None:
            msg = f"Completed {sleep}!"
        time.sleep(sleep)
        print(msg)
        # Wouldn't usually publish to the same queue, but let's keep the demo alive!
        if random.choice([True, False]):
            print("Adding another task for fun...")
            publisher.publish(
                TOPIC, json.dumps({"sleep": random.randint(1, 10)}).encode()
            )

    worker.PubSubWorker(subscriber).run(SUBSCRIPTION, echo)


if __name__ == "__main__":
    demo()
