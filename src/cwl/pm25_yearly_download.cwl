#!/usr/bin/env cwl-runner
### Pipeline to aggregate data in NetCDF format over given geographies
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
  CSV files. This is a wrapper around actual aggregation of
  one file allowing to scatter (parallelize) the aggregation
  over years.

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
    default: [2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017]
  variable:
    type: string
    default:  PM25
  component:
    type: string[]
    default: [BC, NH4, NIT, OM, SO4, SOIL, SS]
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
  database:
    type: File
    doc: Path to database connection file, usually database.ini
  connection_name:
    type: string
    doc: The name of the section in the database.ini file
  table:
    type: string
    doc: The name of the table to store teh aggreagted data in


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
      variable: variable
      component: component
      strategy: strategy
      table: table
    out:
      - shapes
      - aggregate_data
      - consolidated_data
      - aggregate_log
      - aggregate_err
      - data_dictionary

  extract_data_dictionary:
    run:
      class: ExpressionTool
      inputs:
        yaml_files:
          type: File[]
      outputs:
        data_dictionary:
          type: File
      expression: |
        ${
          return {data_dictionary: inputs.yaml_files[0]}
        }
    in:
      yaml_files: process/data_dictionary
    out:
      - data_dictionary

  ingest:
    run: ingest.cwl
    doc: Uploads data into the database
    in:
      registry: extract_data_dictionary/data_dictionary
      domain:
        valueFrom: "exposures"
      table: table
      input: process/aggregate_data
      database: database
      connection_name: connection_name
    out: [log, errors]

  index:
    run: index.cwl
    in:
      depends_on: ingest/log
      registry: extract_data_dictionary/data_dictionary
      domain:
        valueFrom: "exposures"
      table: table
      database: database
      connection_name: connection_name
    out: [log, errors]

  vacuum:
    run: vacuum.cwl
    in:
      depends_on: index/log
      registry: extract_data_dictionary/data_dictionary
      domain:
        valueFrom: "exposures"
      table: table
      database: database
      connection_name: connection_name
    out: [log, errors]



outputs:
  aggregate_data:
    type: File[]
    outputSource: process/aggregate_data
  data_dictionary:
    type: File
    outputSource: extract_data_dictionary/data_dictionary
  consolidated_data:
    type: File[]
    outputSource: process/consolidated_data
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

  ingest_log:
    type: File
    outputSource: ingest/log
  index_log:
    type: File
    outputSource: index/log
  vacuum_log:
    type: File
    outputSource: vacuum/log
  ingest_err:
    type: File
    outputSource: ingest/errors
  index_err:
    type: File
    outputSource: index/errors
  vacuum_err:
    type: File
    outputSource: vacuum/errors
