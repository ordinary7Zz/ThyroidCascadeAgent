#!/usr/bin/env bash
# learned 波次：ZJH-8K + RJH-7K（b3_reinfer 分 chunk 推理 + merge）。
# 默认 GPU 1（与 standard 的 GPU 0 配对）；显存不足可 LEARNED_GPU_CHUNKS=2
export COHORTS="${COHORTS:-zjh8k rjh7k}"
export CUDA_VISIBLE_DEVICES="${LEARNED_GPU_CHUNKS:-1}"
export DEVICE="${DEVICE:-cpu}"
exec "$(dirname "$0")/run_learned_wave3_all.sh"
