import os
from typing import List, Optional
import rasterio

from netCDF4._netCDF4 import Dataset
import shapefile
import numpy
import geopy


def get_atmos_url(year:int, variable ="PM25") -> str:
    """
    Constructs URL to download data from the
    Atmospheric Composition Analysis Group
    given a year and a band

    :param year: year
    :param variable: Gridmet band (variable)
    :return: URL for download
    """

    base = "http://fizz.phys.dal.ca/~atmos/datasets/V4NA03/"
    pattern = base + "V4NA03_{}_NA_{:d}01_{:d}12-RH35.nc"
    return pattern.format(variable, year, year)


def get_nkn_url(variable:str, year:int) -> str:
    """
    Constructs URL to download data from University of Idaho (UI)
    Northwest Knowledge Network
    given a year and a band

    :param year: year
    :param variable: Gridmet band (variable)
    :return: URL for download
    """

    base = "https://www.northwestknowledge.net/metdata/data/"
    pattern = base + "{}_{:d}.nc"
    return pattern.format(variable, year)


def get_shape_file_metadata(shape_file:str, column_names=None) -> List:
    """
    Extracts just metadata columns from a given shapefile

    :param shape_file: a path to a shape file
    :param column_names: a list of column names, default is:
         ["STATE", "ZIP"]
    :return:
    """

    if column_names is None:
        column_names = ["STATE", "ZIP"]
    with shapefile.Reader(shape_file) as shape:
        print(shape)
        shapes = [
            ([getattr(r, c) for c in column_names])
            for r in shape.records()
        ]
    return shapes


def check_shape_file(shapes_dir: str,
                     year: int,
                     geography_type: str,
                     shape_type: str) -> Optional[str]:
    d = os.path.join(shapes_dir, "{:d}".format(year))
    if os.path.isdir(d):
        f = "{}/{}/ESRI{:02d}USZIP5_POLY_WGS84.shp".format(
            geography_type, shape_type,  year - 2000)
        return os.path.join(d, f)
    return None


def find_shape_file(shapes_dir: str, year: int,
                    geography_type: str, shape_type: str) -> str:
    """
    Finds shapefile for a given type of geographies for the
    closest available year

    :param shapes_dir: Directory containing shape files organized as
        ${year}/${geo_type}/{point|polygon}
    :param year: year
    :param geography_type: Geography type, e.g. zip, county, etc.
    :param shape_type: Shape type: polygon, point, etc.
    :return: a shape file for a given year if it exists or for the latest
        year before the given
    """

    shape_file = None
    for d in [-1, 1]:
        y = year
        while (1980 < y < 2021) and (shape_file is None):
            shape_file = check_shape_file(shapes_dir, y, geography_type, shape_type)
            y += d
        if shape_file:
            break
    if shape_file is None:
        raise Exception(
            "Could not find ZIP shape file for year {:d} or earlier"
                .format(year))
    return shape_file

def get_variable(dataset: Dataset,  variable: str):
    """
    Extracts a variable (column) name by a variable "standard name"
    from NCDF4 dataset

    Standard name is a name of a band as described here:
    https://gee.stac.cloud/WUtw2spmec7AM9rk6xMXUtStkMtbviDtHK?t=bands

    A column name is a name of the column in the dataset

    :param dataset: an NCDF4 dataset
    :param variable: "standard name" of a variable, e.g. "tmmx"
    :return:
    """

    standard_name = variable
    for var in dataset.variables.values():
        if hasattr(var,"standard_name") \
                and var.standard_name == standard_name:
            return var.name
    raise Exception("Not found in the dataset: " + standard_name)


def get_days(dataset: Dataset) -> List:
    """
    Extracts a table fo days from NCDF4 dataset

    :param dataset: NCDF4 dataset
    :return: List, containing days
    """

    return dataset["day"][:]


def get_affine_transform(nc_file: str, factor: int = 1):
    """
    Returns affine transformation for a NCDF4 dataset.

    Uses rasterio package: https://rasterio.readthedocs.io/en/latest/index.html

    The `Affine` object is a named tuple with elements
    `a, b, c, d, e, f` corresponding to the elements in
    the matrix equation below, in which a pixel’s image
    coordinates are `x, y` and its world coordinates are `x', y'`

    See more:
    https://rasterio.readthedocs.io/en/latest/topics/georeferencing.html

    :param factor: factor used for disaggregation, None or 0 means
        no disaggregation
    :param nc_file: path to file, containing dataset
    :return: Instance of affine transformation
    """

    with rasterio.open(nc_file) as rio:
        affine = rio.transform
    if factor and factor != 1:
        affine = rasterio.Affine(affine.a / factor,
                                 affine.b,
                                 affine.c,
                                 affine.d,
                                 affine.e / factor,
                                 affine.f
                                 )
    return affine


def disaggregate(layer, factor: int):
    """
    Implementation of R `disaggregate` function with method == ''.

    See details:
    https://www.rdocumentation.org/packages/raster/versions/3.4-5/topics/disaggregate

    or, original source code:

    https://github.com/r-forge/raster/blob/master/pkg/raster/R/disaggregate.R

    :param layer:
    :param factor:
    :return:
    """

    if not factor or factor == 1:
        return layer
    arr = numpy.repeat(layer, factor, axis=0)
    return numpy.repeat(arr, factor, axis=1)


geolocator = geopy.Nominatim(user_agent='NSAPH')
def get_address(latitude:float, longitude: float):
    location = geolocator.reverse((latitude, longitude))
    return location
