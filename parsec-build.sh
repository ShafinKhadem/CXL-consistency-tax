#!/bin/bash

sudo apt install -y build-essential autotools-dev  automake m4 gettext \
                    libx11-dev libxext-dev xorg-dev unzip texinfo \
                    freeglut3-dev cmake debconf-utils build-essential \
                    x11proto-xext-dev libglu1-mesa-dev libxi-dev \
                    libxmu-dev libtbb-dev


export GEM5_PATH="/users/nrkhadem/gem5"
export TARGET_ISA=arm64
export CFLAGS=-I"${GEM5_PATH}/include -static"
export LDFLAGS=-L"${GEM5_PATH}/util/m5/build/${TARGET_ISA}/out"

pushd /users/nrkhadem/parsec-gem5

source env.sh

parsecmgmt -a build -p libtool
parsecmgmt -a build -p hooks
parsecmgmt -a build -p mesa

for NAME in blackscholes bodytrack canneal facesim ferret fluidanimate freqmine streamcluster swaptions vips splash2x.barnes splash2x.cholesky splash2x.fft splash2x.fmm splash2x.lu_cb splash2x.lu_ncb splash2x.ocean_cp splash2x.ocean_ncp splash2x.radiosity splash2x.radix splash2x.volrend splash2x.water_nsquared splash2x.water_spatial; do
    parsecmgmt -a build -p $NAME -c gcc-hooks
done

popd
