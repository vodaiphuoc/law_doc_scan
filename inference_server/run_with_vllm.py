import modal
import os
import sys
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.append(project_root)

from commons.configs.model import ModelConfigQuant
model_config = ModelConfigQuant()

dockerfile_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.6.0-devel-ubuntu20.04",
        add_python= "3.10"
    )
    .pip_install(
        "huggingface_hub[hf_transfer]",
        # "timm",
        "python-dotenv"
    )
    .pip_install(
        f"vllm==0.9.2",
        extra_index_url=f"https://download.pytorch.org/whl/cu126"
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "VLLM_ATTENTION_BACKEND": "FLASH_ATTN"
    })
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
    gpu=f"L4:{N_GPU}",
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
)
@modal.web_server(port=model_config.server_port, startup_timeout=10 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "vllm",
        "serve",
        model_config.model_id,
        "--task","generate",
        "--revision",model_config.model_revision,
        "--api-key",model_config.api_key,
        "--host",model_config.server_name,
        "--port",str(model_config.server_port),
        "--dtype","bfloat16",
        "--max-model-len",str(model_config.max_model_len),
        "--max-num-seqs",str(model_config.max_num_seqs),
        "--limit-mm-per-prompt",model_config.limit_mm_per_prompt,
        "--compilation-config", model_config.compilation_config,
        "--trust-remote-code",
        "--enforce-eager"
    ]

    complete_cmd = " ".join(cmd)

    print(complete_cmd)

    subprocess.Popen(complete_cmd, shell=True)

