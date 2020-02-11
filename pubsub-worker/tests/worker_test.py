import threading
from time import sleep
from unittest.mock import Mock

import pytest

from pubsub_worker import PubSubWorker


def test_handlers(dict_encode):
    data = {"a": 1}
    message = Mock()
    message.data = dict_encode(data)

    def check(a):
        assert a == data["a"], "the arguments should have matched the message"

    message.ack = Mock()
    message.nack = Mock()
    PubSubWorker.nack_errors(PubSubWorker.json_handler(check))(message)
    assert message.ack.call_count == 1, "ack should have been called for no error"
    assert message.nack.call_count == 0, "nack should not have been called for no error"

    def error(a):
        raise ValueError()

    message.ack = Mock()
    message.nack = Mock()
    with pytest.raises(ValueError):
        PubSubWorker.nack_errors(PubSubWorker.json_handler(error))(message)
    assert message.ack.call_count == 0, "ack shouldn't have been called for an error"
    assert message.nack.call_count == 1, "nack should have been called for an error"


def test_start(dict_encode, test_queue, subscriber, publisher):
    items = {1, 2, 3}
    for v in items:
        publisher.publish(test_queue["topic"], dict_encode({"v": v}))
    collected = {"i": 0, "items": set()}
    lock = threading.Lock()

    def handler(v):
        with lock:
            collected["i"] += 1
            collected["items"].add(v)

    runner = PubSubWorker(subscriber=subscriber).start(test_queue["sub"], handler)
    # Wait for the runner local buffer to fill and handlers to complete (with a
    # timeout), but exit early if we're done.
    timeleft, step = 5, 1
    while timeleft:
        timeleft -= step
        sleep(step)
        with lock:
            if collected["i"] == len(items):
                break
    runner.cancel()
    assert items == collected["items"], "The collected items does not match the input!"
