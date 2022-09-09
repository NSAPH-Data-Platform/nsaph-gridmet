import logging
import os
import re

from nsaph import init_logging

from gridmet.config import GridmetContext
from pollution.aggregator import Aggregator


class WUSTLFile:
    def __init__(self, context: GridmetContext = None):
        """
        Creates a new instance

        :param context: An optional GridmetContext object, if not specified,
            then it is constructed from the command line arguments
        """

        init_logging(name="wustl-aggregation", level=logging.INFO)
        if not context:
            context = GridmetContext(__doc__).instantiate()
        self.context = context
        self.aggregator = None
        self.infile = self.context.raw_downloads
        self.year = None
        self.month = None
        return

    def parse_file_name(self):
        m = re.search("([1|2][0-9]{3}[0|1][0-9])_\\1", self.infile)
        if not m:
            raise ValueError("File name: {} does not match expected pattern"
                             .format(self.infile))
        ym = m.group(1)
        self.year = ym[:4]
        self.month = ym[4:]

    def prepare(self):
        if not self.infile.endswith(".nc"):
            raise ValueError("NetCDF file is expected (extension .nc)")
        self.parse_file_name()
        extra_columns = ["Year", "Month"], [self.year, self.month]
        of, _ = os.path.splitext(self.infile)
        of += ".csv"
        if self.context.compress:
            of += ".gz"

        if len(self.context.shape_files) != 1:
            raise ValueError("Shape type is required and only one "
                             "shape type is allowed for aggregation."
                             "len(self.context.shape_files)={:d}"
                             .format(len(self.context.shape_files)))
        shape_file = self.context.shape_files[0]
        self.aggregator = Aggregator(
            infile=self.infile,
            variable="PM25",
            outfile=of,
            strategy=self.context.strategy,
            shapefile=shape_file,
            geography=self.context.geography,
            extra_columns=extra_columns
        )
        return

    def execute(self):
        self.aggregator.execute()
        print("Aggregation of data from {} by {} has been executed".format(
            self.infile,
            self.context.geography.value
        ))


if __name__ == '__main__':
    task = WUSTLFile()
    task.prepare()
    task.execute()

