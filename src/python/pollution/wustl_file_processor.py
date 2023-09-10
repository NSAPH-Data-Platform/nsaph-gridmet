import re

from gridmet.netCDF_file_processor import NetCDFFile

from gridmet.config import GridContext


class WUSTLFile(NetCDFFile):
    def __init__(self, context: GridContext = None):
        """
        Creates a new instance

        :param context: An optional GridmetContext object, if not specified,
            then it is constructed from the command line arguments
        """

        super().__init__(context)
        self.year = None
        self.month = None
        return

    def parse_file_name(self):
        m = re.search("([1|2][0-9]{3}[0|1][0-9])_\\1", self.infile)
        if m:
            ym = m.group(1)
            self.year = ym[:4]
            self.month = ym[4:]
            return
        m = re.search("([1|2][0-9]{3})[0|1][0-9]_\\1[0|1][0-9]", self.infile)
        if m:
            ym = m.group(1)
            self.year = ym[:4]
            return 
        raise ValueError("File name: {} does not match expected pattern"
                             .format(self.infile))

    def on_prepare(self):
        if self.extra_columns is not None:
            raise ValueError("For NetCDF files downloaded from WUSTL, extra columns cannot "
                             "be provided by user as they are calculated automatically")
        self.parse_file_name()
        if self.year is not None:
            if self.month is not None:
                self.extra_columns = ["Year", "Month"], [self.year, self.month]
            else:
                self.extra_columns = ["Year"], [self.year]
        else:
            self.extra_columns = None
        return


if __name__ == '__main__':
    task = WUSTLFile()
    task.prepare()
    task.execute()

