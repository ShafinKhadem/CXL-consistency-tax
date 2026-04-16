# To run blackscholes of parsec:

sudo sysctl kernel.perf_event_paranoid=1

./gem5/build/ALL/gem5.opt ./x86-parsec-benchmarks.py --benchmark blackscholes --size simsmall

# Build workload images

Modify https://github.com/gem5/gem5-resources/tree/c1ee9d33e81043c5bbbc29d7ac7d89d6ae34c4a9/src/gapbs to install parsec using this script: https://github.com/PSCurlin/gem5-resources/blob/a5967cae468a684226606db055e74957b5cbee29/parsec/scripts/install-parsec.sh
