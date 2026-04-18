#!/bin/bash

PARSEC_DIR="/home/shafin/repos/parsec-gem5"

declare -A exp_simsize=(
    [blackscholes]="simdev"
    [swaptions]="simlarge"
    [freqmine]="simdev"
)

for NAME in "${!exp_simsize[@]}"; do
    simsize=${exp_simsize[$NAME]}
    echo "Extracting input_$simsize.tar for $NAME..."
    TAR_PATH="$PARSEC_DIR/parsec-3.0/pkgs/apps/$NAME/inputs/input_$simsize.tar"

    if [ -f "$TAR_PATH" ]; then
        tar -xf "$TAR_PATH"
    fi

    export NTHREADS=1
    source $PARSEC_DIR/config/packages/parsec.$NAME.pkgconf
    source $PARSEC_DIR/pkgs/${pkg_group}/$NAME/parsec/$simsize.runconf
    echo "Running $NAME with $simsize configuration..."
    ./gem5/build/ALL/gem5.opt se_binary_workload.py --binary-path $PARSEC_DIR/pkgs/${pkg_group}/$NAME/inst/amd64-linux.gcc-hooks/bin/$NAME --binary-args "${run_args}"
done
