#!/usr/bin/env cwl-runner
### Workflow to aggregate and ingest NetCDF files for one year
#  Copyright (c) 2021-2022. Harvard University
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

cwlVersion: v1.2
class: Workflow

requirements:
  SubworkflowFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}
  ScatterFeatureRequirement: {}
  MultipleInputFeatureRequirement: {}


doc: |
  Sub-workflow to aggregate a NetCDF file for one year over a given
  geography (zip codes or counties). Before aggregation, downloads
  shape files fo this year from US Census website

inputs:
  depends_on:
    type: Any?
  proxy:
    type: string?
    default: ""
    doc: HTTP/HTTPS Proxy if required
  downloads:
    type: Directory
  geography:
    type: string
  band:
    type: string
  year:
    type: int
  strategy:
    type: string
    doc: "Rasterization strategy"
  shape_file_collection:
    type: string
    default: tiger
    doc: |
      [Collection of shapefiles](https://www2.census.gov/geo/tiger), 
      either GENZ or TIGER

steps:
  get_shapes:
    run: get_shapes.cwl
    in:
      year:
        valueFrom: $(String(inputs.yy))
      yy: year
      geo: geography
      collection: shape_file_collection
      proxy: proxy
    out:
      - shape_files

  findfile:
    doc: |
      Given input directory, variable (band), year and month,
      evaluates the exepected file name for the input data
    run:
      class: ExpressionTool
      inputs:
        downloads:
          type: Directory
        year:
          type: int
        band:
          type: string
      expression: |
        ${
          var v = inputs.band.toUpperCase();
          var y = String(inputs.year);
          var f;
          if (v == 'PM25') {
            f = "V4NA03_" + v + "_NA_" + y + "01_" + y + "12-RH35.nc";
          } else {
            v = inputs.band;
            if (y == '2017') {
              f = "GWRwSPEC.HEI_" + v + "_NA_" + y + "01_" + y + "12-wrtSPECtotal.nc"
            } else {
              f = "GWRwSPEC_" + v + "_NA_" + y + "01_" + y + "12-wrtSPECtotal.nc"
            };
          };
          f = inputs.downloads.location + '/' + f;
          return {
            netcdf_file: {
              "class": "File",
              "location": f
            }
          };
        }
      outputs:
        netcdf_file:
          type: File
    in:
      year: year
      band: band
      downloads: downloads
    out: [netcdf_file]

  aggregate:
    doc: Aggregate data over geographies
    run: wustl_aggregate.cwl
    in:
      strategy: strategy
      geography: geography
      netcdf_data: findfile/netcdf_file
      shape_files: get_shapes/shape_files
      band: band
    out:
      - log
      - errors
      - csv_data

outputs:
  shapes:
    type: File[]
    outputSource: get_shapes/shape_files

  aggregate_data:
    type: File
    outputSource: aggregate/csv_data
  aggregate_log:
    type: File?
    outputSource: aggregate/log
  aggregate_err:
    type: File
    outputSource: aggregate/errors






