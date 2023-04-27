#  Copyright (c) 2023. Harvard University
#
#  Developed by Research Software Engineering,
#  Harvard University Research Computing
#  and The Harvard T.H. Chan School of Public Health
#  Authors: Michael A Bouzinier, Kezia Irene, Michelle Audirac
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


"""
See:

https://unidata.github.io/netcdf4-python/
https://neetinayak.medium.com/combine-many-netcdf-files-into-a-single-file-with-python-469ba476fc14
https://docs.xarray.dev/en/stable/api.html

"""
import argparse
import logging
from typing import Optional, List

from netCDF4 import Dataset

from nsaph import init_logging


class NetCDFDataset:
    """
    Class to combine NetCDF dataset with absolute values with
    dependent datasets containing components
    """
    def __int__(self):
        self.dataset: Optional[Dataset] = None
        self.main_var: Optional[str] = None
        '''The name of the main variable'''
        self.percentages: List[str] = []
        '''The names of the component variables containing percentages'''
        self.abs_values: List[str] = []
        '''The names of the component variables containing absolute values'''

        return

    def read_abs_values(self, filename: str, var: str = None):
        """
        Reads the NetCDF dataset from a *.nc file
        Assumes that this dataset contains absolute values of
        the variable with the name provided by var parameter.

        Raises an exception if the variable is not None but is not present n the dataset.
        If the parameter "var" is None, checks that there is only one variable present beside "lat" and "lon".
        Raises exception if there is more than one variable

        :param var: The variable containing the absolute values of the feature of interest, e.g., "pm25"
            If None, defaults to a single variable present in teh dataset beside "lat" and "lon"
        :param filename: A path to file to read.
            Can also be a python 3 pathlib instance or the URL of an OpenDAP dataset.
        :raises: ValueError if var is None and there is more than one variable in the dataset or, if var
            is not None and is not present in teh dataset
        """

        return

    def add_component(self, filename: str, var: str = None, abs_var: str = None):
        """
        Reads the NetCDF dataset from a *.nc file
        Assumes that this dataset contains percentage of a component defined by
        the var parameter.

        Can only be called after the dataset is initialized with absolute values.

        :param var: The variable containing percentage of a certain component
        :param abs_var: The variable name to contain absolute values of the component. If omitted,
            it is constructed from the percentage variable name either by removing 'p' if the
            variable starts with 'p' otherwise, by adding 'abs_' prefix
        :param filename: A path to file to read.
            Can also be a python 3 pathlib instance or the URL of an OpenDAP dataset.
        :raises: ValueError if var is None and there is more than one variable in the dataset or, if var
            is not None and is not present in the dataset
        :raises: ValueError if the grid of the component file is incompatible with
            the gird of the existing Dataset
        :raises: ValueError if the absolute values have not yet been read
        """

        return

    def add_components(self, filenames: List[str]):
        """
        Adds multiple components in a single call from multiple files. Assumes that
        every file given contains only one variable beside lat and lon

        Can only be called after the dataset is initialized with absolute values.

        :param filenames:  A list of file paths to read.
            Elements of the list can also be a python 3 pathlib instance or the URL of an OpenDAP dataset.
        :raises: ValueError if there is more than one variable in any of the datasets
        :raises: ValueError if the grid of a component file is incompatible with
            the gird of the existing Dataset
        :raises: ValueError if the absolute values have not yet been read
        """

        return

    def compute_abs_values(self):
        """
        Computes absolute values for every component present in the dataset.
        :raises: ValueError if the absolute values have not yet been read
        """

    def get_dataset(self) -> Dataset:
        return self.dataset

    def write_dataset(self, filename):
        """
        Creates a new file or overwrites existing one saving the current state of the dataset

        :param filename:
        :return:
        """

        return

    def __str__(self):
        """
        Constructs string representation of the dataset, with variable names and dimensional information
        """
        return super()


def main(infile: str, components: List[str], outfile):
    ds = NetCDFDataset()
    print(ds)
    ds.read_abs_values(infile)
    print(ds)
    ds.add_components(components)
    print(ds)
    ds.compute_abs_values()
    print(ds)
    if outfile:
        ds.write_dataset(outfile)


if __name__ == '__main__':
    init_logging(level=logging.INFO, name="NetCDF")
    parser = argparse.ArgumentParser (description="Tool to combine components into a single NetCDF file")
    parser.add_argument("--input", "-in", "-i",
                        help="Path to the main NetCDF file containing absolute values",
                        default=None,
                        required=True)
    parser.add_argument("--components", "-c",
                        help="Path to the NetCDF files containing components",
                        nargs='+',
                        default=None,
                        required=True)
    parser.add_argument("--output", "-out", "-o",
                        help="Path to the file with the combined dataset",
                        default=None,
                        required=False)

    args = parser.parse_args()
    main(args.input, args.components, args.output)



