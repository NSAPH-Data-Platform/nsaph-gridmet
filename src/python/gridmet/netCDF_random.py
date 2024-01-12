"""
Reaself.ds a NetCDF file (*.nc) and prints some information
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
from typing import List, Tuple, Dict

import netCDF4 as nc
import random

from gridmet.gridmet_tools import get_address


class NCViewer:
    def __init__(self, fn, smp = 10):
        self.ds = nc.Dataset(fn)
        self.variables = list(self.ds.variables.keys())
        self.dimensions = self.ds.dimensions
        self.geovars = []
        self.nongeovars = []
        self.lat_var = None
        self.lon_var = None
        self.lat = None
        self.lon = None
        self.sample_size = smp
        self.center_point = dict()

        for var in self.variables:
            if var.lower() == "lat":
                self.lat_var = var
            elif var.lower() == "lon":
                self.lon_var = var
        if self.lat_var:
            self.lat = self.ds[self.lat_var]
        if self.lon_var:
            self.lon = self.ds[self.lon_var]

        for var in self.variables:
            try:
                f = 0
                for d in self.ds[var].dimensions:
                    if d == self.lat_var:
                        f += 1
                    if d == self.lon_var:
                        f += 1
                if f >= 2:
                    self.geovars.append(var)
                elif var not in [self.lat_var, self.lon_var]:
                    self.nongeovars.append(var)
            except:
                print("Exception processing: " + var)

        return

    def print_var(self, var: str):
        var_dim = ','.join(self.ds[var].dimensions)
        print("Variable: {}; Dimensions: {}".format(var, var_dim))

    def print(self):
        print("Latitude var: " + self.lat_var)
        print("Latitude var: " + self.lon_var)
        print("=== Geographical variables:")
        for var in self.geovars:
            self.print_var(var)
        print("=== Non geographical variables: ")
        for var in self.nongeovars:
            self.print_var(var)

    def print_metadata(self):
        print(self.ds)
        return

    def print_random_values(self):
        for v in self.geovars:
            layer = self.ds[v]
            ldims = layer.dimensions
            for i in range(0, self.sample_size):
                value = layer
                print(v + ": ", end='')
                for dim in ldims:
                    vdim = random.randrange(0, self.dimensions[dim].size)
                    value = value[vdim]
                    sv = str(self.ds[dim][vdim])
                    print("{}={}: ".format(dim, sv), end='')
                print(value)
        return

    def random_lat_lon(self) -> List[Tuple[int, int]]:
        values = []
        for i in range(0, self.sample_size):
            lo = random.randrange(0, len(self.lon))
            la = random.randrange(0, len(self.lat))
            values.append((la, lo))
        return values

    def get_value(self, t: Dict, var: str):
        layer = self.ds[var]
        value = layer
        for d in layer.dimensions:
            value = value[t[d]]
        return value

    def get_anchor(self, t: Dict):
        dims = []
        for d in self.dimensions:
            sv = str(self.ds[d][t[d]])
            dims.append("{}={}".format(d, sv))
        return ": ".join(dims)

    def gen_random_dimensions(self) -> List[Dict]:
        dims = []
        for i in range(self.sample_size):
            t = dict()
            for d in self.dimensions:
                if d in self.center_point:
                    v = self.center_point[d]
                else:
                    v = (random.randrange(0, self.dimensions[d].size))
                t[d] = v
            dims.append(t)
        return dims

    def generate_area(self) -> List[Dict]:
        dims = []
        l1 = self.center_point[self.lat_var]
        l2 = self.dimensions[self.lat_var].size
        lba = int(max(0, l1 - self.sample_size/2))
        uba = int(min(l1 + self.sample_size/2, l2))
        l1 = self.center_point[self.lon_var]
        l2 = self.dimensions[self.lon_var].size
        lbo = int(max(0, l1 - self.sample_size/2))
        ubo = int(min(l1 + self.sample_size/2, l2))
        for lat in range(lba, uba):
            for lon in range(lbo, ubo):
                t = dict()
                t[self.lat_var] = lat
                t[self.lon_var] = lon
                for d in self.dimensions:
                    if d in [self.lat_var, self.lon_var]:
                        continue
                    if d in self.center_point:
                        v = self.center_point[d]
                    else:
                        v = (random.randrange(0, self.dimensions[d].size))
                    t[d] = v
                dims.append(t)
        return dims

    def print_by_geography(self, points: List[Dict]):
        for t in points:
            la = t[self.lat_var]
            lo = t[self.lon_var]
            address = get_address(float(self.lat[la]), float(self.lon[lo]))
            anchor = self.get_anchor(t)
            values = []
            for var in self.geovars:
                values.append(var + "=" + str(self.get_value(t, var)))
            data = anchor + ": " + ", ".join(values)
            if address is not None:
                data += "; Address: " + str(address)
            print(data)

    def find(self, dim: str, val: str):
        if dim == "lat":
            x1 = self.ds.geospatial_lat_min
            dx = self.ds.geospatial_lat_resolution
        elif dim == "lon":
            x1 = self.ds.geospatial_lon_min
            dx = self.ds.geospatial_lon_resolution
        else:
            raise ValueError("How to set " + dim)
        dval = float(val)
        x1 = float(x1)
        dx = float(dx)
        d = int((dval - x1) / dx)
        if dval - d > (dx/2):
            d += 1
        if float(self.ds[dim][1]) < float(self.ds[dim][0]):
            d = self.ds[dim].shape[0] - d
        return d


    def set_args(self, argv: List[str]):
        for i in range(1, len(sys.argv)):
            arg = sys.argv[i]
            if arg.startswith("--") and i < len(sys.argv) - 1:
                x = arg[2:]
                y = sys.argv[i+1]
                if x == "day":
                    y = int(y)
                elif x in ["lat", "lon"]:
                    y = self.find(x, y)
                self.center_point[x] = y


if __name__ == '__main__':
    fn = sys.argv[1]
    if len(sys.argv) > 2:
        sample_size = int(sys.argv[2])
    else:
        sample_size = 20
    random.seed(0)
    viewer = NCViewer(fn, sample_size)
    viewer.print()
    if len(viewer.geovars) < 1:
        print("No variables in the dataset")
        exit(0)

    viewer.set_args(argv=sys.argv[1:])
    if viewer.lon_var in viewer.center_point:
        viewer.print_by_geography(viewer.generate_area())
    else:
        viewer.print_by_geography(viewer.gen_random_dimensions())








