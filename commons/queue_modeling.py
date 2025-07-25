import aio_pika
from typing import Callable, Coroutine, Any
import asyncio
import loguru
import json

from aio_pika.abc import (
    AbstractRobustConnection, 
    AbstractRobustChannel, 
    AbstractIncomingMessage
)

from configs.apis import MQ_SETTINGS

class _QueueBase(object):
    def __init__(
            self, 
            user:str,
            pwd: str,
            host_name:str, 
            port: int
        ):
        self._url = f"amqp://{user}:{pwd}@{host_name}:{port}"

class QueueProducer(_QueueBase):
    connection: AbstractRobustConnection | None = None
    channel: AbstractRobustChannel | None = None

    def __init__(
            self, 
            user: str, 
            pwd: str, 
            host_name:str, 
            port: int, 
            service_logger: loguru._logger.Logger
        )->None:
        super().__init__(user = user, pwd=pwd, host_name= host_name, port= port)
        self._logger = service_logger

    def status(self) -> bool:
        if self.connection.is_closed or self.channel.is_closed:
            return False
        return True

    async def _clear(self) -> None:
        if not self.channel.is_closed:
            await self.channel.close()
        if not self.connection.is_closed:
            await self.connection.close()

        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        """
        Establish connection with the RabbitMQ

        :return: None
        """
        self._logger.info("connect to rabbitmq...")
        try:
            self.connection = await aio_pika.connect_robust(self._url)
            self.channel = await self.connection.channel(publisher_confirms=False)
            self._logger.info("rabbitmq is connected")
        
        except Exception as e:
            await self._clear()
            self._logger.error(e.__dict__)

    async def disconnect(self) -> None:
        """
        Disconnect and clear connections from RabbitMQ

        :return: None
        """
        await self._clear()

    async def send_messages(
            self,
            messages: list | dict,
            routing_key: str
    ) -> None:
        if routing_key not in [MQ_SETTINGS.EXTRACT_SERVICE_QUEUE_NAME, MQ_SETTINGS.RANKING_SERVICE_QUEUE_NAME]:
            raise ValueError("`routing key` must be one of \
                `MQ_SETTINGS.EXTRACT_SERVICE_QUEUE_NAME` or `MQ_SETTINGS.RANKING_SERVICE_QUEUE_NAME`")
        
        if not self.channel:
            raise RuntimeError("Cannot connect to rabbitmq")

        if isinstance(messages, dict):
            messages = [messages]

        async with self.channel.transaction():
            for message in messages:
                message = aio_pika.Message(
                    body=json.dumps(message).encode()
                )

                await self.channel.default_exchange.publish(
                    message, routing_key=routing_key,
                )


class QueueConsumer(_QueueBase):
    def __init__(
            self,
            queue_name:str,
            call_back: Callable[[AbstractIncomingMessage, Any, Any], Coroutine[None, None, None]],
            service_logger: loguru._logger.Logger,
            user:str,
            pwd: str,
            host_name:str, 
            port: int,
            *args,
            **kwargs
        )->None:
        super().__init__(user = user, pwd=pwd, host_name= host_name, port= port)
        self._queue_name = queue_name
        self._call_back = call_back
        self._logger = service_logger
        self._args = args
        self._kwargs = kwargs

    async def _run_queue(self) -> None:
        connection = await aio_pika.connect_robust(self._url)
        try:
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=2)
                queue = await channel.declare_queue(self._queue_name, auto_delete=True)

                self._logger.info("start")
                
                await queue.consume(self._call_back, *self._args, **self._kwargs)

                await asyncio.Future()

        except aio_pika.exceptions.AMQPConnectionError as e:
            self._logger.error(f"Failed to connect to RabbitMQ: {e}")
            # Depending on your error handling strategy, you might want to
            # implement a retry mechanism here.
        except asyncio.CancelledError:
            self._logger.info("RabbitMQ consumer task was cancelled.")
        except Exception as e:
            self._logger.error(f"An unexpected error occurred in the run_queue task: {e}")
        finally:
            if connection and not connection.is_closed:
                self._logger.info("Closing RabbitMQ connection...")
                await connection.close()
                self._logger.info("RabbitMQ connection closed.")


    def start_background_task(self, loop: asyncio.AbstractEventLoop):
        self.rabbitmq_handler_task = loop.create_task(self._run_queue())

    async def stop_background_task(self):
        if self.rabbitmq_handler_task and not self.rabbitmq_handler_task.done():
            self.rabbitmq_handler_task.cancel()
            # Optionally, wait for the task to actually finish cancelling
            try:
                await asyncio.wait_for(self.rabbitmq_handler_task, timeout=5.0) # Wait max 5 seconds for cleanup
            except asyncio.TimeoutError:
                self._logger.warning("Background task did not finish cancelling within timeout.")
            except asyncio.CancelledError:
                self._logger.info("Background task confirmed cancelled.")
            except Exception as e:
                self._logger.error(f"Error during background task cancellation wait: {e}")
        else:
            self._logger.info("No background task to cancel or task already done.")