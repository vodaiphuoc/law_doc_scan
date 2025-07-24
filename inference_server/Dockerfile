
ARG CUDA_VERSION=12.6.0
ARG BUILD_BASE_IMAGE=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu20.04

FROM ${BUILD_BASE_IMAGE}

ARG VLLM_VERSION=0.9.2
ARG FLASHINFER_GIT_REPO=https://github.com/flashinfer-ai/flashinfer.git
ARG FLASHINFER_GIT_REF=v0.2.8rc1
ARG FI_TORCH_CUDA_ARCH_LIST="7.5 8.0 8.9 9.0a"

RUN apt-get update && apt-get install -y python3 python3-pip git
RUN python3 -m pip install uv

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install huggingface_hub[hf_transfer] 
# RUN pip3 install vllm==0.9.2

RUN echo ${VLLM_VERSION}

RUN git clone --depth 1 --recursive --shallow-submodules \
        --branch ${FLASHINFER_GIT_REF} \
        ${FLASHINFER_GIT_REPO} flashinfer
    
# build AOT kernels
RUN ls && cd flashinfer
RUN export TORCH_CUDA_ARCH_LIST="${FI_TORCH_CUDA_ARCH_LIST}" && python3 -m flashinfer.aot
RUN export TORCH_CUDA_ARCH_LIST="${FI_TORCH_CUDA_ARCH_LIST}" && uv pip install --system --no-build-isolation .
RUN cd .. && rm -rf flashinfer


COPY ../commons /app/commons