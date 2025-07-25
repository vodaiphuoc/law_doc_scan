import json
import os
from typing import List,Union
import uuid

from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    APIRouter, 
    HTTPException, 
    Response,
    Depends,
    status,
    Request,
    UploadFile
)
from fastapi.responses import JSONResponse

from common import (
    make_logger,
    Firebase_Client, 
    QueueProducer,
    MQ_SETTINGS
)

ServiceLogger = make_logger("APP service | User router")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.storage = Firebase_Client(service_name= 'App service')

    app.queue_producer = QueueProducer(
        user = MQ_SETTINGS.USER, 
        pwd = MQ_SETTINGS.PWD, 
        host_name = MQ_SETTINGS.HOSTNAME, 
        port = MQ_SETTINGS.PORT,
        service_logger= ServiceLogger
    )
    await app.queue_producer.connect()

    yield
    app.storage = None
    await app.queue_producer.disconnect()

USER_ROUTER = APIRouter(lifespan = lifespan)


@USER_ROUTER.post("/upload")
async def upload_file(
        pdfInputs: UploadFile,
        request: Request,
        # db: Session = Depends(get_db), 
        user_id: int  = 1 #= Depends(get_current_user_id)
    ):
    r"""
    Main router for `USER_ROUTER`.
    The workflow includes:
        - handling user upload file
        - add data into relation db
        - add files into Firebase (object storage)
        - return status to UI immediately (no waiting for transcript files)
    """
    
    content = await pdfInputs.read()
    try:
        extract_task_data = request.app.storage.upload_pdf(
            user_id = user_id,
            file_name = str(uuid.uuid4()) + pdfInputs.filename,
            file_content = content
        )
        ServiceLogger.info("Done upload to storage")
    except Exception as e:
        ServiceLogger.error("Error in upload to storage")
        return JSONResponse(content= "Server error", status_code= 404)
    
    try:
        await request.app.queue_producer.send_messages(
            messages = extract_task_data,
            routing_key = MQ_SETTINGS.EXTRACT_SERVICE_QUEUE_NAME
        )
        ServiceLogger.info("Done send message to queue")
    except Exception as e:
        ServiceLogger.error("Error in sending message to queue")
        return JSONResponse(content= "Server error", status_code= 404)
    
    return JSONResponse(content= {"message": "Successfully upload your CV"})