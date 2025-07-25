import sys
import os
import asyncio
import tempfile

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from aio_pika.abc import AbstractIncomingMessage


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.append(project_root)


from .model_client import ModelWrapperClient
from commons.configs.model import ModelConfigQuant
from commons.logger import get_logger
from commons.configs.apis import (
    MQ_SETTINGS,
    GENERAL_SETTINGS
)
from commons.schemas.mq_messages import ScanRequest
from commons.queue_modeling import QueueConsumer
from commons.database_storage import DB_Storage_Client

SERVICE_NAME = "Extract service"
ServiceLogger = get_logger(SERVICE_NAME)
TEMP_DATA_PATH = __file__.replace("app.py",".temp_data")


async def message_handler(
        message: AbstractIncomingMessage,
        engine: ModelWrapperClient,
        storage_client: DB_Storage_Client
    ) -> None:
    r"""
    Callback function for handling scan file request
    """
    
    async with message.process():
        # extract data
        msg: str = message.body.decode()
        req_data: ScanRequest = ScanRequest.model_validate_json(msg)

        ServiceLogger.info('receive data from queue: {msg}'.format(msg = msg))

        # process with temporary file
        with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                mode='wb', 
                delete=True, 
            ) as temp_pdf_file:

            file_content = storage_client.download_pdf(
                bucket_name=req_data.remote_path, 
                remote_path=req_data.remote_path
            )

            temp_pdf_file.write(file_content)

            # Ensure all data is written to disk before accessing via its name
            temp_pdf_file.flush()
            os.fsync(temp_pdf_file.fileno())

            # Get the path to the temporary PDF file
            temp_pdf_path = temp_pdf_file.name
            
            extract_result = await engine.forward(
                local_path_pdf= temp_pdf_path,
                task = req_data.task
            )

        if extract_result is None:
            ServiceLogger.info('failed to extract data')
        else:
            ...


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    loop = asyncio.get_event_loop()
    # model_engine = ModelInference()

    engine = ModelWrapperClient(config= ModelConfigQuant())

    storage_client = DB_Storage_Client()

    queue_client = QueueConsumer(
        user = MQ_SETTINGS.USER,
        pwd = MQ_SETTINGS.PWD, 
        host_name = MQ_SETTINGS.HOSTNAME, 
        port = MQ_SETTINGS.PORT,
        queue_name = MQ_SETTINGS.RANKING_SERVICE_QUEUE_NAME,
        call_back = message_handler,
        service_logger = ServiceLogger,
        engine = engine,
        storage_client = storage_client
    )

    queue_client.start_background_task(loop)

    ServiceLogger.info('app done init')
    yield
    ServiceLogger.info('app shutting down. Cancelling background task...')
    await queue_client.stop_background_task()
    ServiceLogger.info('app shutdown complete.')


main_app = FastAPI(lifespan= lifespan)

@main_app.get("/")
async def index():
    return JSONResponse("hello word from scan service")

async def main():
    config = uvicorn.Config("app:app",
                            host = GENERAL_SETTINGS.APPLICATION_HOST,
                            port = GENERAL_SETTINGS.EXTRACT_SERVICE_PORT,
                            reload = True,
                            log_level = "info"
                            )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())

