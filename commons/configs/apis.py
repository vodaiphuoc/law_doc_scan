from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json

def read_env(key:str, extend_key:str|None= None)->str:
    _file_path = os.environ[key]

    if not os.path.isfile(_file_path):
        raise Exception(f"input path file: {_file_path}, is not valid")
    
    with open(_file_path, 'r') as fp:
        data = fp.read()
    
    dict_data = {
        line.split("=")[0].strip(): line.split("=")[1].strip()  
        for line in data.split("\n") if line != ""
    }

    if extend_key:
        dict_data[extend_key] = os.environ[key+'_E']
    
    return json.dumps(dict_data)

class _OBJS_Setting_Model(BaseModel):
    r"""Object storage settings"""
    DB_URL:str
    StorageBucketURL: str
    ACCOUNT_KEY_FILE: str
    PROJECT_ID: str

class _RabbitMQ_Setting_Model(BaseModel):
    r"""RabbitMQ settings"""
    USER:str
    PWD:str
    HOSTNAME:str
    PORT:int
    EXTRACT_SERVICE_QUEUE_NAME:str
    RANKING_SERVICE_QUEUE_NAME:str

class _General_Setting_Model(BaseModel):
    G_API_KEY:str
    APPLICATION_HOST: str
    APP_SERVICE_PORT:int
    EXTRACT_SERVICE_PORT:int
    RANKING_SERVICE_PORT:int

load_dotenv("config.env")

OBJS_SETTINGS = _OBJS_Setting_Model.model_validate_json(read_env('OBJS', 'ACCOUNT_KEY_FILE'))
MQ_SETTINGS = _RabbitMQ_Setting_Model.model_validate_json(read_env('MQ'))
GENERAL_SETTINGS = _General_Setting_Model.model_validate_json(read_env('GENERAL'))