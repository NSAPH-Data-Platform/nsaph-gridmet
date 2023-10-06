"""
Reads a NetCDF file (*.nc) and prints some information
about it
"""

#  Copyright (c) 2021. Harvard University
#
#  Developed by Research Software Engineering,
#  Faculty of Arts and Sciences, Research Computing (FAS RC)
#  Author: Michael A Bouzinier
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import sys

import netCDF4 as nc
import random

from gridmet.gridmet_tools import get_address

if __name__ == '__main__':
    fn = sys.argv[1]
    if len(sys.argv) > 2:
        size = int(sys.argv[2])
    else:
        size = 20
    ds = nc.Dataset(fn)
    print(ds)

    lat = ds["LAT"]
    lon = ds["LON"]
    random.seed(0)
    variables = list(ds.variables.keys())
    variables.remove("LAT")
    variables.remove("LON")
    if len(variables) < 1:
        raise ValueError("No variables in the dataset")

    fmt = "[{:d},{:d}]: ({:f}, {:f}: {}) "
    layers = {v: ds[v] for v in variables}
    for i in range(0, size):
        lo = random.randrange(0, len(lon))
        la = random.randrange(0, len(lat))
        address = get_address(float(lat[la]), float(lon[lo]))
        values = ["{}: {}".format(v, layers[v][la, lo]) for v in layers]
        data = fmt.format(lo, la, lat[la], lon[lo], values)
        if address is not None:
            data += "; Address: " + str(address)
        print(data)


