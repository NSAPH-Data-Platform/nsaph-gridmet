import logging
import os
import re
import warnings
from typing import Optional

from nsaph import init_logging
from nsaph_gis.compute_shape import StatsCounter

from gridmet.config import GridContext
from gridmet.aggregator import Aggregator, GeoTiffAggregator, NetCDFAggregator

"""
An entry point to a command line utility aggregating grid data
provided as NetCDF file over a set of shape files, assigning
labels defined in the shape files to teh aggregated values


`see https://www.unidata.ucar.edu/software/netcdf/`__ 
"""


class NetCDFFile:
    def __init__(self, context: GridContext = None):
        """
        Creates a new instance

        :param context: An optional GridmetContext object, if not specified,
            then it is constructed from the command line arguments
        """

        if not context:
            context = GridContext(doc=__doc__).instantiate()
        self.context = context
        self.file_type = None
        log = os.path.basename(self.context.raw_downloads).split('.')[0]
        init_logging(
            name="aggr-" + log,
            level=logging.INFO
        )
        self.aggregator: Optional[Aggregator] = None
        self.infile = self.context.raw_downloads
        self.extra_columns = None
        StatsCounter.statistics = context.statistics
        return

    def on_prepare(self):
        """
        This method can be overwritten by subclasses
        to configure proper aggregation
        """

        pass

    def prepare(self):
        if self.infile.endswith(".nc"):
            self.file_type = "nc"
            aggregator = NetCDFAggregator
        elif self.infile.endswith(".tif") or self.infile.endswith(".tiff"):
            self.file_type = 'tiff'
            aggregator = GeoTiffAggregator
        else:
            raise ValueError("NetCDF file is expected (extension .nc)")
        self.on_prepare()
        of, _ = os.path.splitext(os.path.basename(self.infile))
        of += '_' + self.context.geography.value + ".csv"
        if not os.path.isdir(self.context.destination):
            os.makedirs(self.context.destination, exist_ok=True)
        of = os.path.join(self.context.destination, of)
        if self.context.compress:
            of += ".gz"

        if len(self.context.shape_files) != 1:
            raise ValueError("Shape type is required and only one "
                             "shape type is allowed for aggregation."
                             "len(self.context.shape_files)={:d}"
                             .format(len(self.context.shape_files)))
        shape_file = self.context.shape_files[0]
        if len(self.context.variables) > 0:
            variable = self.context.variables
        else:
            raise ValueError("No variables are specified")
        self.aggregator = aggregator(
            infile=self.infile,
            variable=variable,
            outfile=of,
            strategy=self.context.strategy,
            shapefile=shape_file,
            geography=self.context.geography,
            extra_columns=self.extra_columns
        )
        return

    def execute(self):
        # warnings.simplefilter("error")
        if os.path.isfile(self.infile):
            self.aggregator.execute()
            print(
                "Aggregation of data from {} by {} has been executed. Output: {}"
                    .format(
                        self.infile,
                        self.context.geography.value,
                        self.aggregator.outfile
            ))
        else:
            of = self.aggregator.write_header()
            print("Input file was not found. Created empty file: {}".format(of))
        return


if __name__ == '__main__':
    task = NetCDFFile()
    task.prepare()
    task.execute()

