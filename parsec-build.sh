#!/bin/bash

export GEM5_PATH="/users/nrkhadem/gem5"
export TARGET_ISA=arm64
export CFLAGS=-I"${GEM5_PATH}/include"
export LDFLAGS=-L"${GEM5_PATH}/util/m5/build/${TARGET_ISA}/out"
export CXXFLAGS="-static"

pushd /users/nrkhadem/parsec-gem5

source env.sh

parsecmgmt -a build -p libtool
parsecmgmt -a build -p hooks
parsecmgmt -a build -p mesa

for NAME in blackscholes bodytrack facesim fluidanimate freqmine streamcluster swaptions; do
    parsecmgmt -a build -p $NAME -c gcc-hooks
done

popd
