import modal

dockerfile_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "lmdeploy",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})  # faster model transfers
)

app = modal.App("Inference-server-internVL3")

N_GPU = 1
MINUTES = 60  # seconds unit
HTTP_PORT = 8000
MODEL_NAME = "OpenGVLab/InternVL3-1B"
MODEL_REVISION="main"

@app.function(
    image=dockerfile_image,
    gpu=f"T4:{N_GPU}",
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
)
@modal.web_server(port=HTTP_PORT, startup_timeout=10 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "lmdeploy",
        "serve",
        "api_server",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--tp",
        "1",
        "--session-len",
        "16384",
        "--quant-policy",
        "8"
    ]

    print(cmd)

    subprocess.Popen(" ".join(cmd), shell=True)

