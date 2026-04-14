# To run blackscholes of parsec:

sudo sysctl kernel.perf_event_paranoid=1

export GEM5_RESOURCE_JSON=./resources.json

./gem5/build/ALL/gem5.opt ./x86-parsec-benchmarks.py --benchmark blackscholes --size simsmall
