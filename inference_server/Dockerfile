FROM openmmlab/lmdeploy:latest

RUN apt-get update && apt-get install -y python3 python3-pip git

WORKDIR /app

RUN pip3 install --upgrade pip

CMD ["lmdeploy", "serve", "api_server", "OpenGVLab/InternVL3-1B", "--tp","1","--session_len","16384","--quant_policy","8"]