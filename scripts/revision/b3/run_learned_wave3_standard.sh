#!/usr/bin/env bash
# learned 波次：OpenThyroid + PKTN + DDTI（不含 ZJH/RJH 大队列 chunk）。
# 默认 GPU 0；覆盖：LEARNED_GPU_STANDARD=3 bash ...
export COHORTS="tn5k thyroidxl pktn ddti_seg ddti_cls"
export CUDA_VISIBLE_DEVICES="${LEARNED_GPU_STANDARD:-0}"
export DEVICE="${DEVICE:-cuda}"
exec "$(dirname "$0")/run_learned_wave3_all.sh"
