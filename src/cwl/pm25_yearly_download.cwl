#!/usr/bin/env cwl-runner
### Pipeline to ingest Pollution downloaded from WashU Box
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
  Workflow to aggregate pollution data coming in NetCDF format
  over given geographies (zip codes or counties) and output as 
  CSV files

inputs:
  proxy:
    type: string?
    default: ""
    doc: HTTP/HTTPS Proxy if required
  downloads:
    type: Directory
    doc: Directory, containing files, downloaded and unpacked from WUSTL box
  geography:
    type: string
    doc: |
      Type of geography: zip codes or counties
      Valid values: "zip", "zcta" or "county"
  years:
    type: int[]
    default: [2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018]
  band:
    type: string
    default: pm25
  strategy:
    type: string
    default: downscale
    doc: "Rasterization strategy"
  shape_file_collection:
    type: string
    default: tiger
    doc: |
      [Collection of shapefiles](https://www2.census.gov/geo/tiger), 
      either GENZ or TIGER

steps:
  process:
    doc: Downloads raw data and aggregates it over shapes and time
    scatter:
      - year
    run: aggregate_one_file.cwl
    in:
      proxy: proxy
      downloads: downloads
      geography: geography
      shape_file_collection: shape_file_collection
      year: years
      band: band
      strategy: strategy
    out:
      - shapes
      - aggregate_data
      - aggregate_log
      - aggregate_err



outputs:
  data:
    type: File[]
    outputSource: process/aggregate_data
  shapes:
    type:
      type: array
      items:
        type: array
        items: [File]
    outputSource: process/shapes

  aggregate_log:
    type:
      type: array
      items: Any

    outputSource: process/aggregate_log
  aggregate_err:
    type: File[]
    outputSource: process/aggregate_err

