#!/bin/bash

export GEM5_PATH="/users/nrkhadem/gem5"
export TARGET_ISA=arm64
export CFLAGS=-I"${GEM5_PATH}/include -static"
export LDFLAGS=-L"${GEM5_PATH}/util/m5/build/${TARGET_ISA}/out"

pushd /users/nrkhadem/parsec-gem5

source env.sh

parsecmgmt -a build -p libtool
parsecmgmt -a build -p hooks
parsecmgmt -a build -p mesa

for NAME in blackscholes bodytrack canneal facesim ferret fluidanimate freqmine streamcluster swaptions vips; do
    parsecmgmt -a build -p $NAME -c gcc-hooks
done

popd
