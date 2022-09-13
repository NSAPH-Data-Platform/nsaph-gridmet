import logging
import os
import re
from typing import Optional

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

        if not context:
            context = GridmetContext(__doc__).instantiate()
        self.context = context
        log = os.path.basename(self.context.raw_downloads).split('.')[0]
        init_logging(
            name="aggr-" + log,
            level=logging.INFO
        )
        self.aggregator: Optional[Aggregator] = None
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
        of, _ = os.path.splitext(os.path.basename(self.infile))
        of += ".csv"
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
    task = WUSTLFile()
    task.prepare()
    task.execute()

