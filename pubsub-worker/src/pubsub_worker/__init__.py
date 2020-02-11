""" Simple Pub/Sub based worker.
"""
import dataclasses as dc
import json
import signal
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler

Handler = Callable
MessageHandler = Callable[[Message], None]


@dc.dataclass
class PubSubWorker:
    """ Worker implementation leveraging Google Pub/Sub.
    """

    subscriber: pubsub_v1.SubscriberClient = dc.field(
        default_factory=pubsub_v1.SubscriberClient
    )

    @classmethod
    def ack_errors(cls, fn: MessageHandler) -> MessageHandler:
        """ Ack unhandled errors, but maintains the exception.
        """

        def wrapped(message):
            try:
                fn(message)
            finally:
                message.ack()

        return wrapped

    @staticmethod
    def nack_errors(fn: MessageHandler) -> MessageHandler:
        """ Acks unhandled errors, but maintains the exception.
        """

        def wrapped(message):
            try:
                fn(message)
            except Exception:
                message.nack()
                raise
            else:
                message.ack()

        return wrapped

    @classmethod
    def parse_json(cls, message):
        return json.loads(message.data.decode())

    @classmethod
    def json_handler(cls, fn: Handler) -> MessageHandler:
        """ Default MessageHandler unpacking json to kwargs.
        """
        return lambda message: fn(**cls.parse_json(message))

    @staticmethod
    def _make_scheduler(max_workers: int):
        """ Makes a scheduler with limited workers.

            The executor logic was ripped/trimmed from https://bit.ly/2O3jUso
        """
        return ThreadScheduler(
            executor=ThreadPoolExecutor(
                max_workers=max_workers, thread_name_prefix="callback-handler"
            )
        )

    def run(self, subscription: str, callback: Handler, **kwargs: Any):
        """ Start and wait for a signal to stop.
        """
        self.wait(self.start(subscription, callback, **kwargs))

    def start(self, subscription: str, callback: Handler, **kwargs: Any):
        """ Wrap a normal python function with a JSON message handler.

            To prevent errors from propagating, the callback is wrapped with ack_errors
            to prevent errors from propagating. If you need different behavior, use
            start_messege_handler directly.
        """
        return self.start_messege_handler(
            subscription, self.ack_errors(self.json_handler(callback)), **kwargs
        )

    def start_messege_handler(
        self, subscription: str, callback: MessageHandler, max_workers: int = 10
    ) -> StreamingPullFuture:
        """
            Start working on this PubSub subscription.

            Set `max_workers` to limit the number of threads working in parallel. Handlers
            that aren't safe for concurrent use should set this to 1.

            It is the callback's responsibility to ack/nack the message.
        """
        return self.subscriber.subscribe(
            subscription, callback, scheduler=self._make_scheduler(max_workers)
        )

    @staticmethod
    def wait(runner: StreamingPullFuture):
        """ Wait for the worker and cancel on interruption.
        """

        def cancel(*args):
            print("Shutting down...")
            runner.cancel()

        signal.signal(signal.SIGINT, cancel)
        signal.signal(signal.SIGTERM, cancel)
        try:
            runner.result()
        except Exception:
            cancel()
            raise
