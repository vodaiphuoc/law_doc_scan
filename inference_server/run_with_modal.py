import modal

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.append(project_root)

from commons.configs.model import ModelConfig

model_config = ModelConfig()

dockerfile_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "lmdeploy",
        "huggingface_hub[hf_transfer]",
        "timm"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})  # faster model transfers
    .add_local_dir("commons", remote_path= "/root/commons")
)

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

app = modal.App("Inference-server-internVL3")

N_GPU = 1
MINUTES = 60  # seconds unit

@app.function(
    image=dockerfile_image,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
    },
    gpu=f"T4:{N_GPU}",
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
)
@modal.web_server(port=model_config.server_port, startup_timeout=10 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "lmdeploy",
        "serve",
        "api_server", model_config.model_id,
        "--revision",model_config.model_revision,
        "--backend",model_config.backend,
        "--api-keys",model_config.api_key,
        "--server-name",model_config.server_name,
        "--server-port",str(model_config.server_port),
        "--tp",str(model_config.tp),
        "--session-len",str(model_config.session_len),
        "--quant-policy",str(model_config.quant_policy)
    ]

    print(cmd)

    subprocess.Popen(" ".join(cmd), shell=True)

