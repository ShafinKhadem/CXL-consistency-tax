#!/bin/bash

for write_ratio in 50 25 75 0 100; do
  for isa in ARM X86; do
    for lsqsize in 8 16 32 64 128; do
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
