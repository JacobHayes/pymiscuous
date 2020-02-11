import json
import warnings
from uuid import uuid4

from google.cloud import pubsub_v1

import pytest

PROJECT = "<your project>"
if PROJECT == "<your project>":
    raise ValueError("Set the PROJECT variable in tests/conftest.py!")

# Ignore Google Cloud cred warnings when working locally.
warnings.filterwarnings(
    "ignore", "Your application has authenticated using end user credentials"
)


@pytest.fixture(scope="session")
def project():
    return PROJECT


@pytest.fixture(scope="session")
def publisher():
    return pubsub_v1.PublisherClient()


@pytest.fixture(scope="session")
def subscriber():
    return pubsub_v1.SubscriberClient()


@pytest.fixture(scope="session")
def t(project):
    return lambda topic: f"projects/{project}/topics/{topic}"


@pytest.fixture(scope="session")
def s(project):
    return lambda subscription: f"projects/{project}/subscriptions/{subscription}"


@pytest.fixture
def test_queue(publisher, subscriber, t, s):
    """ Create a new test queue and worker and teardown afterwards.
    """
    topic, subscription = t(f"test-{uuid4()}"), s(f"test-{uuid4()}")
    publisher.create_topic(topic)
    subscriber.create_subscription(subscription, topic)
    yield {"sub": subscription, "topic": topic}
    subscriber.delete_subscription(subscription)
    publisher.delete_topic(topic)


@pytest.fixture(scope="session")
def dict_encode():
    return lambda d: json.dumps(d).encode()
