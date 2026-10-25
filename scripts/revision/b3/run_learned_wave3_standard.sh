#!/usr/bin/env bash
# learned 波次：OpenThyroid + PKTN + DDTI（不含 ZJH/RJH 大队列 chunk）。
export COHORTS="tn5k thyroidxl pktn ddti_seg ddti_cls"
exec "$(dirname "$0")/run_learned_wave3_all.sh"
