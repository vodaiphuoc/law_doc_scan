# from uuid import uuid4
# from fastapi import UploadFile, Request, FastAPI
# from fastapi.responses import JSONResponse
# import uvicorn
# import os
# from typing import List, Dict, Union, Any
# from types import NoneType
# from contextlib import asynccontextmanager
# from dotenv import load_dotenv
# import asyncio
# import json
# from aio_pika.abc import AbstractIncomingMessage

# # from .components import pdf2imgs, UnslothExtractModel
# from commons import (
#     QueueConsumer, 
#     make_logger,
#     ExtractModelResult,
#     Firebase_Client,
#     MQ_SETTINGS,
#     GENERAL_SETTINGS
# )

# SERVICE_NAME = "Extract service"
# ServiceLogger = make_logger(SERVICE_NAME)
# TEMP_DATA_PATH = __file__.replace("app.py",".temp_data")

# class ModelInference(object):
#     def __init__(self):
#         self.engine = UnslothExtractModel()
#         self.pdf2imgs = pdf2imgs
    
#     def run(self, file_path: str)->Dict[str, Union[str, bool, NoneType, Dict[str, Any]]]:
#         api_response_data = None

#         img_paths = self.pdf2imgs(file_path, resize= False)

#         _results = self.engine.forward(img_paths = img_paths)
#         print('_results: ', _results)

#         if _results['status']:
#             api_response_data = {
#                 "status": _results['status'],
#                 "msg": _results['msg'],
#                 "result": _results['result'].model_dump_json(indent = 2)
#             }
#         else:
#             api_response_data = {
#                 "status": _results['status'],
#                 "msg": _results['msg'],
#                 "result": None
#             }

#         # empty temporary data
#         os.remove(file_path)
#         for _img_path in img_paths:
#             os.remove(_img_path)
    
#         return api_response_data

# async def message_handler(
#         message: AbstractIncomingMessage,
#         model_instance: ModelInference,
#         storage_client: Firebase_Client
#     ) -> None:

#     # extract data
#     async with message.process():
#         body_data = json.loads(message.body.decode())
#         ServiceLogger.info('receive data from queue: {msg}'.format(msg = body_data))

#         # parsing data
#         _temp_local_file = f'{TEMP_DATA_PATH}/temp_write_{"_".join(body_data["blob_name"].split(os.sep))}'
#         storage_client.download_blob(**body_data, destination_file_name = _temp_local_file)


#         extract_result = model_instance.run(_temp_local_file)
        

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     load_dotenv()
#     loop = asyncio.get_event_loop()
#     model_engine = ModelInference()
#     storage_client = Firebase_Client(service_name= SERVICE_NAME)

#     queue_client = QueueConsumer(
#         user = MQ_SETTINGS.USER, 
#         pwd = MQ_SETTINGS.PWD, 
#         host_name = MQ_SETTINGS.HOSTNAME, 
#         port = MQ_SETTINGS.PORT,
#         queue_name = MQ_SETTINGS.RANKING_SERVICE_QUEUE_NAME,
#         call_back = message_handler,
#         service_logger = ServiceLogger,
#         model_instance = model_engine,
#         storage_client = storage_client
#     )

#     queue_client.start_background_task(loop)

#     ServiceLogger.info('app done init')
#     yield
#     ServiceLogger.info('app shutting down. Cancelling background task...')
#     await queue_client.stop_background_task()
#     ServiceLogger.info('app shutdown complete.')


# main_app = FastAPI(lifespan= lifespan, root_path="extract_service")

# @main_app.get("/")
# async def index():
#     return JSONResponse("hello word from extract service")

# async def main():
#     config = uvicorn.Config("app:app",
#                             host = GENERAL_SETTINGS.APPLICATION_HOST,
#                             port = GENERAL_SETTINGS.EXTRACT_SERVICE_PORT,
#                             reload = True,
#                             log_level = "info"
#                             )
#     server = uvicorn.Server(config)
#     await server.serve()

# if __name__ == "__main__":
#     asyncio.run(main())


import sys
import os
import argparse
import asyncio

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.append(project_root)

from model.infer import ModelWrapperClient
from commons.configs.model import ModelConfigQuant

engine = ModelWrapperClient(config= ModelConfigQuant())

async def main(args):
    await engine.forward(local_path_pdf = args.file_path)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path")
    args = parser.parse_args()
    
    asyncio.run(main(args))