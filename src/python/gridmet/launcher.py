"""
    Executing pipelines through this class requires a collection of shape files
    corresponding to geographies for which data is aggregated
    (for example, zip code areas or counties).

    The data has to be placed in the following directory structure:
    ${year}/${geo_type: zip|county|etc.}/${shape:point|polygon}/

    Which geography is used is defined by `geography` argument that defaults
    to "zip". Only actually used geographies must have their shape files
    for the years actually used.

    Output file format:
    At the moment output is a simple 3+ columns file (most files contain 3
    columns, but parameter “metadata” can define more columns to include):

    1. Variable (aka band) mean value. The actual band is given in the arguments
       (or configuration object) and is printed in the header line of the file

    2. Date in YYYY-mm-dd format (SQL date format)

    3. Label, associated with location. E.g., zip code for zip shapes,
       county fips for county shapes or custom label for point file.
       For points file, the label is taken from the first column defined by
       “metadata” argument.

    4+. If more than one column is included in metadata, the output file
        will contain more than 3 columns
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

import logging
from typing import List

from nsaph import init_logging

from gridmet.config import GridmetContext
from gridmet.task import GridmetTask


class Gridmet:
    """
    Main class, describes the whole download and processing job for climate data

    The pipeline consists of the collection of Task Objects
    """

    def __init__(self, context: GridmetContext = None):
        """
        Creates a new instance

        :param context: An optional GridmetContext object, if not specified,
            then it is constructed from the command line arguments
        """

        init_logging(name="gridMET-Download", level=logging.INFO)
        if not context:
            context = GridmetContext(__doc__).instantiate()
        self.context = context
        self.tasks = self.collect_tasks()

    def collect_tasks(self) -> List:
        tasks = [
            GridmetTask(self.context, y, v)
                for y in self.context.years for v in self.context.variables
        ]
        return tasks

    def execute_sequentially(self):
        """
        Executes all tasks in the pipeline sequentially
        without any parallelization
        :return: None
        """

        for task in self.tasks:
            task.execute()


if __name__ == '__main__':
    gridmet = Gridmet()
    gridmet.execute_sequentially()
    print("All tasks have been executed")
