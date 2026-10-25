#!/usr/bin/env bash
# learned 波次：ZJH-8K + RJH-7K（b3_reinfer 分 chunk 推理 + merge）。
export COHORTS="zjh8k rjh7k"
exec "$(dirname "$0")/run_learned_wave3_all.sh"
