#!/usr/bin/env python

class RAIVariation:
    """
    Class containing all the RAI test cases
    """
    DISTORTION1 = 'REGULAR_D1'
    REGULAR = 'REGULAR'
    DISTORTION2 = 'REGULAR_D2'
    DISTORTION3 = 'REGULAR_D3'
    WEATHER = 'REGULAR_W'
    SHIFT = 'REGULAR_S'

# RAI_CASES to be used
RAI_CASES = [RAIVariation.REGULAR, RAIVariation.SHIFT, RAIVariation.DISTORTION3, RAIVariation.WEATHER, RAIVariation.DISTORTION2, \
            RAIVariation.DISTORTION1]