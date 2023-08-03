"""
API to aggregate data over shapes

The Aggregator class expects a netCDF dataset, containing 3 variables:
value, latitude and longitude
"""
import abc
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
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple, Set, Any

import rasterio
from netCDF4 import Dataset
from nsaph import init_logging
from nsaph_gis.compute_shape import StatsCounter
from nsaph_gis.constants import RasterizationStrategy, Geography
from nsaph_utils.utils.io_utils import fopen, CSVWriter, Collector

from gridmet.gridmet_tools import get_affine_transform, disaggregate


class Aggregator(ABC):
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
        self.dataset: Dataset = None
        if isinstance(variable, list):
            self.aggr_variables = variable
        else:
            self.aggr_variables = [str(variable)]
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
        self.open()
        variables = self.get_dataset_variables()

        for v in variables:
            if v in self.aggr_variables:
                return
        lv = [v.lower() for v in self.aggr_variables]
        for v in variables:
            if v.lower() in lv:
                idx = lv.index(v.lower())
                self.aggr_variables[idx] = v
                return

        vvv = [v for v in variables if v.lower() not in ['lat', 'lon']]
        raise ValueError(
            "Variable {} not found in the file {}. Available variables: {}"
            .format(self.aggr_variables, self.infile, ','.join(vvv))
        )

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def get_dataset_variables(self) -> Set[str]:
        pass

    @abstractmethod
    def get_layer(self, var):
        pass

    def write_header(self):
        with fopen(self.outfile, "wt") as out:
            writer = CSVWriter(out)
            key = self.geography.value.lower()
            headers = self.aggr_variables + [key]
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
        layers = [self.get_layer(var) for var in self.aggr_variables]
        t1 = datetime.now()
        self.compute(collector, layers)
        collector.flush()
        t3 = datetime.now()
        t = datetime.now() - t0
        logging.info(" \t{} [{}]".format(str(t3 - t1), str(t)))

    def downscale(self, layer):
        if self.factor > 1:
            logging.info("Downscaling by the factor of " + str(self.factor))
            layer = disaggregate(layer, self.factor)
        else:
            layer = layer[:]
        return layer

    def compute(self, writer: Collector, layers):
        fid, _ = os.path.splitext(os.path.basename(self.infile))
        now = datetime.now()
        logging.info(
            "%s:%s:%s: %s",
            str(now),
            self.geography.value,
            self.aggr_variables,
            fid
        )

        if len(layers) == 1:
            layer = layers[0]
            for record in StatsCounter.process(
                    self.strategy,
                    self.shapefile,
                    self.affine,
                    layer,
                    self.geography
            ):
                row = [record.value, record.prop]
                if self.extra_values:
                    row += self.extra_values
                writer.writerow(row)
            logging.info(
                "%s: %s completed in %s", str(datetime.now()),
                fid,
                str(datetime.now() - now)
            )
        else:
            for record in StatsCounter.process_layers(
                    self.strategy,
                    self.shapefile,
                    self.affine,
                    layers,
                    self.geography
            ):
                row: List[Any] = [v for v in record.values]
                row.append(record.prop)
                if self.extra_values:
                    row += self.extra_values
                writer.writerow(row)
            logging.info(
                "%s: %s completed in %s", str(datetime.now()),
                fid,
                str(datetime.now() - now)
            )


class NetCDFAggregator(Aggregator):
    def open(self):
        self.dataset = Dataset(self.infile)

    def get_dataset_variables(self) -> Set[str]:
        return set(self.dataset.variables)

    def get_layer(self, var):
        logging.info("Extracting layer: " + var)
        return self.downscale(self.dataset[var])


class GeoTiffAggregator(Aggregator):

    def __init__(self, infile: str, variable: str, outfile: str,
                 strategy: RasterizationStrategy, shapefile: str,
                 geography: Geography,
                 extra_columns: Tuple[List[str], List[str]] = None):
        super().__init__(infile, variable, outfile, strategy, shapefile,
                         geography, extra_columns)
        self.array = None

    def open(self):
        self.dataset = rasterio.open(self.infile)
        self.array = self.dataset.read()

    def get_dataset_variables(self) -> Set[str]:
        return set(self.dataset.descriptions)

    def get_layer(self, var):
        logging.info("Extracting layer: " + var)
        if var not in self.dataset.descriptions:
            raise ValueError(f'Variable {var} is not in the dataset')
        idx = self.dataset.descriptions.index(var)
        return self.downscale(self.array[idx])

if __name__ == '__main__':
    init_logging(level=logging.INFO)
    fn = sys.argv[1]
    if not fn.endswith(".nc"):
        raise ValueError("NetCDF file is expected (extension .nc)")
    sf = sys.argv[2]
    of, _ = os.path.splitext(fn)
    of += ".csv.gz"
    a = NetCDFAggregator(
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

