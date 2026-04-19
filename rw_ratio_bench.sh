#!/bin/bash

for write_ratio in 50 25 75 0 100; do
  for isa in ARM X86; do
    for sqsize in 8 16 32 64 128 1; do
      lqsize=$sqsize
      if [ "$sqsize" -eq 1 ]; then
        lqsize=128
      fi
      echo "Running with ISA=$isa, SQ size=$sqsize, LQ size=$lqsize, write-ratio=$write_ratio"
      ./gem5/build/ALL/gem5.opt rw_ratio_bench.py \
        --binary-path rw_ratio_bench-${isa} \
        --isa "$isa" \
        --sq-size "$sqsize" \
        --lq-size "$lqsize" \
        --write-ratio "$write_ratio"
    done
  done
done
