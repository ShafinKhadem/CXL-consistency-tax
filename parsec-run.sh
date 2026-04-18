#!/bin/bash

PARSEC_DIR="/home/shafin/repos/parsec-gem5"

declare -A exp_simsize=(
    [blackscholes]="simdev"
    [swaptions]="simlarge"
    [freqmine]="simdev"
)

exp_order=("blackscholes" "swaptions" "freqmine") # bash doesn't preserve order of map keys, so we define an array to specify the order of experiments

for NAME in "${exp_order[@]}"; do
    simsize=${exp_simsize[$NAME]}

    export NTHREADS=1
    source $PARSEC_DIR/config/packages/parsec.$NAME.pkgconf
    exppkgdir="$PARSEC_DIR/pkgs/${pkg_group}/$NAME"
    source $exppkgdir/parsec/$simsize.runconf

    echo "Extracting input_$simsize.tar for $NAME..."
    TAR_PATH="$exppkgdir/inputs/input_$simsize.tar"

    if [ -f "$TAR_PATH" ]; then
        tar -xf "$TAR_PATH"
    fi

    echo "Running $NAME with $simsize configuration..."
    arch=$(uname -m)
    if [ "$arch" == "x86_64" ]; then
        ./gem5/build/ALL/gem5.opt se_binary_workload.py --binary-path $exppkgdir/inst/amd64-linux.gcc-hooks/bin/$NAME --binary-args "${run_args}"
    elif [ "$arch" == "aarch64" ]; then
        ./gem5/build/ALL/gem5.opt se_binary_workload.py --isa ARM --binary-path $exppkgdir/inst/aarch64-linux.gcc-hooks/bin/$NAME --binary-args "${run_args}"
    else
        echo "Unsupported architecture: $arch"
        exit 1
    fi
done
