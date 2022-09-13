"""
API to aggregate data over shapes

The Aggregator class expects a netCDF dataset, containing 3 variables:
value, latitude and longitude
"""


#  Copyright (c) 2022. Harvard University
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
import logging
import os
import sys
from datetime import datetime
from typing import List, Tuple

from netCDF4 import Dataset
from nsaph import init_logging
from nsaph_gis.compute_shape import StatsCounter
from nsaph_gis.constants import RasterizationStrategy, Geography
from nsaph_utils.utils.io_utils import fopen, CSVWriter, Collector

from gridmet.gridmet_tools import get_affine_transform, disaggregate


class Aggregator:
    def __init__(self,
                 infile: str,
                 variable: str,
                 outfile: str,
                 strategy: RasterizationStrategy,
                 shapefile: str,
                 geography: Geography,
                 extra_columns: Tuple[List[str], List[str]] = None):
        self.infile = infile
        self.outfile = outfile
        self.factor = 1
        self.affine = None
        self.dataset = None
        self.variable = variable
        if strategy == RasterizationStrategy.downscale:
            self.factor = 5

        self.strategy = strategy
        self.shapefile = shapefile
        self.geography = geography
        if extra_columns:
            self.extra_headers, self.extra_values = extra_columns
        else:
            self.extra_headers, self.extra_values = None, None

    def prepare(self):
        if not self.affine:
            self.affine = get_affine_transform(self.infile, self.factor)
        logging.info("%s => %s", self.infile, self.outfile)
        self.dataset = Dataset(self.infile)

    def write_header(self):
        with fopen(self.outfile, "wt") as out:
            writer = CSVWriter(out)
            key = self.geography.value.lower()
            headers = [self.variable, key]
            if self.extra_headers:
                headers += self.extra_headers
            writer.writerow(headers)
        return self.outfile

    def execute(self, mode: str = "wt"):
        """
        Executes computational task

        :param mode: mode to use opening result file
        :type mode: str
        :return:
        """

        self.prepare()
        if 'a' not in mode:
            self.write_header()
            if 't' in mode:
                mode = 'at'
            else:
                mode = 'a'
        with fopen(self.outfile, mode) as out:
            writer = CSVWriter(out)
            self.collect_data(writer)

    def collect_data(self, collector: Collector):
        t0 = datetime.now()
        layer = self.dataset[self.variable]   #[:, :]
        t1 = datetime.now()
        self.compute(collector, layer)
        collector.flush()
        t3 = datetime.now()
        t = datetime.now() - t0
        logging.info(" \t{} [{}]".format(str(t3 - t1), str(t)))

    def compute(self, writer: Collector, layer):
        if self.factor > 1:
            layer = disaggregate(layer, self.factor)

        fid, _ = os.path.splitext(os.path.basename(self.infile))
        now = datetime.now()
        logging.info(
            "%s:%s:%s: %s",
            str(now),
            self.geography.value,
            self.variable,
            fid
        )

        for record in StatsCounter.process(self.strategy, self.shapefile, self.affine, layer, self.geography):
            row = [record.mean, record.prop]
            if self.extra_values:
                row += self.extra_values
            writer.writerow(row)
        logging.info(
            "%s: %s completed in %s", str(datetime.now()),
            fid,
            str(datetime.now() - now)
        )


if __name__ == '__main__':
    init_logging(level=logging.INFO)
    fn = sys.argv[1]
    if not fn.endswith(".nc"):
        raise ValueError("NetCDF file is expected (extension .nc)")
    sf = sys.argv[2]
    of, _ = os.path.splitext(fn)
    of += ".csv.gz"
    a = Aggregator(
        infile=fn,
        variable="PM25",
        outfile=of,
        strategy=RasterizationStrategy.downscale,
        shapefile=sf,
        geography=Geography.county,
        extra_columns=(["Year", "Month"], ["2018", "12"])
    )
    a.execute()
    print("All Done")

