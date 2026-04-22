#!/bin/bash

for write_ratio in 0 100 50 25 75; do
  for isa in ARM; do
    for needstso in true false; do
      for sqsize in 8 16 32 64 128; do
        lqsize=$sqsize
        echo "Running with ISA=$isa, SQ size=$sqsize, LQ size=$lqsize, write-ratio=$write_ratio, TSO=$needstso"
        ./gem5/build/ALL/gem5.opt rw_ratio_bench.py \
          --binary-path rw_ratio_bench-${isa} \
          --isa "$isa" \
          --sq-size "$sqsize" \
          --lq-size "$lqsize" \
          --write-ratio "$write_ratio" \
          $( [ "$needstso" = true ] && echo "--needs-tso" )
      done
    done
  done
done
