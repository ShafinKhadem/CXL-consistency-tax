# -*- coding: utf-8 -*-
# Copyright (c) 2016 Jason Lowe-Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Jason Lowe-Power
# Updated for gem5 25.1 stable release

"""Cache hierarchy definitions for gem5 25.1

This module provides a configurable cache hierarchy using gem5's classic
memory model. Each core has private L1 instruction and data caches.
"""

from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)


class CacheHierarchy(PrivateL1CacheHierarchy):
    """
    A simple private L1 cache hierarchy using the classic memory model.

    Each core has private L1 instruction and data caches with configurable sizes.
    """

    def __init__(self, options=None):
        """
        Initialize the cache hierarchy.

        Parameters
        ----------
        options : object, optional
            Options object with cache configuration parameters
        """
        # Get cache sizes from options or use defaults
        l1i_size = "32KiB"
        l1d_size = "32KiB"

        if options:
            if hasattr(options, "l1i_size") and options.l1i_size:
                l1i_size = options.l1i_size
            if hasattr(options, "l1d_size") and options.l1d_size:
                l1d_size = options.l1d_size

        super().__init__(
            l1d_size=l1d_size,
            l1i_size=l1i_size,
        )
