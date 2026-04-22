#!/bin/bash

PARSEC_DIR="/home/shafin/repos/parsec-gem5"

declare -A exp_simsize=(
    [blackscholes]="simdev"
    [swaptions]="simdev"
    [canneal]="simdev"
    [freqmine]="simdev"
    [fluidanimate]="test"
    [ferret]="test"
    [splash2x.fft]="simdev"
)

exp_order=("blackscholes" "swaptions" "canneal" "fluidanimate" "ferret" "splash2x.fft") # bash doesn't preserve order of map keys, so we define an array to specify the order of experiments

for NAME in "${exp_order[@]}"; do
    simsize=${exp_simsize[$NAME]}

    export NTHREADS=1

    if [[ $NAME == splash2x.* ]]; then
        NAME="${NAME#splash2x.}"
        source $PARSEC_DIR/config/packages/splash2x.$NAME.pkgconf
        exppkgdir="$PARSEC_DIR/ext/splash2x/${pkg_group}/$NAME"
    else
        source $PARSEC_DIR/config/packages/parsec.$NAME.pkgconf
        exppkgdir="$PARSEC_DIR/pkgs/${pkg_group}/$NAME"
    fi
    source $exppkgdir/parsec/$simsize.runconf

    echo "Extracting input_$simsize.tar for $NAME..."
    TAR_PATH="$exppkgdir/inputs/input_$simsize.tar"

    if [ -f "$TAR_PATH" ]; then
        tar -xf "$TAR_PATH"
    fi

    echo "Running $NAME with $simsize configuration..."
    
    ./gem5/build/ALL/gem5.opt se_binary_workload.py --isa ARM --binary-path $exppkgdir/inst/aarch64-linux.gcc-hooks/bin/$NAME --binary-args "${run_args}" --num-cores=1
    ./gem5/build/ALL/gem5.opt se_binary_workload.py --isa ARM --binary-path $exppkgdir/inst/aarch64-linux.gcc-hooks/bin/$NAME --binary-args "${run_args}" --num-cores=1 --needs-tso
done
