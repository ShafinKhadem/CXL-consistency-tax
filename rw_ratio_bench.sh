#!/bin/bash

for isa in X86 ARM; do
  for lsqsize in 16 32 64 128 256; do
    for write_ratio in 0 25 50 75 100; do
      echo "Running with ISA=$isa, SQ/LQ size=$lsqsize, write-ratio=$write_ratio"
      ./gem5/build/ALL/gem5.opt rw_ratio_bench.py \
        --binary-path rw_ratio_bench-${isa} \
        --isa "$isa" \
        --sq-size "$lsqsize" \
        --lq-size "$lsqsize" \
        --write-ratio "$write_ratio"
    done
  done
done
