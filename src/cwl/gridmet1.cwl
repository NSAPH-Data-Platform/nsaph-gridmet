#!/usr/bin/env cwl-runner
### gridMET Pipeline
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

cwlVersion: v1.2
class: Workflow

requirements:
  SubworkflowFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}
  ScatterFeatureRequirement: {}
  MultipleInputFeatureRequirement: {}

doc: |
  Downloads, processes gridMET data and ingests it into the database

inputs:
  proxy:
    type: string?
    default: ""
    doc: HTTP/HTTPS Proxy if required
  shapes:
    type: Directory
  geography:
    type: string
    doc: |
      Type of geography: zip codes or counties
  years:
    type: string[]
    default: ['2009', '2010']
  bands:
    type: string[]
    default: ['rmax', 'rmin', 'sph', 'srad', 'th', 'tmmn', 'tmmx']
  database:
    type: File
    doc: Path to database connection file, usually database.ini
  connection_name:
    type: string
    doc: The name of the section in the database.ini file
  dates:
    type: string?
    doc: 'dates restriction, for testing purposes only'


steps:
  registry:
    run: registry.cwl
    doc: Writes down YAML file with the database model
    in: []
    out:
      - model
      - log
      - errors

  process:
    scatter: band
    in:
      proxy: proxy
      model: registry/model
      shapes: shapes
      geography: geography
      years: years
      dates: dates
      band: bands
      database: database
      connection_name: connection_name
      table:
        valueFrom: $(inputs.geography + '_' + inputs.band)

    run:
      class: Workflow
      inputs:
        proxy:
          type: string?
        model:
          type: File
        shapes:
          type: Directory
        geography:
          type: string
        years:
          type: string[]
        band:
          type: string
        table:
          type: string
        database:
          type: File
        connection_name:
          type: string
        dates:
          type: string?
      steps:
        download:
          run: download.cwl
          doc: Downloads and processes data
          scatter: year
          scatterMethod:  nested_crossproduct
          in:
            proxy: proxy
            shapes: shapes
            geography: geography
            year: years
            dates: dates
            band: band
          out:
            - data
            - log
            - errors

        ingest:
          run: ingest.cwl
          doc: Uploads data into the database
          in:
            registry: model
            table: table
            input: download/data
            database: database
            connection_name: connection_name
          out: [log, errors]

        index:
          run: index.cwl
          in:
            depends_on: ingest/log
            registry: model
            domain:
              valueFrom: "gridmet"
            table: table
            database: database
            connection_name: connection_name
          out: [log, errors]

        vacuum:
          run: vacuum.cwl
          in:
            depends_on: index/log
            domain:
              valueFrom: "gridmet"
            registry: model
            table: table
            database: database
            connection_name: connection_name
          out: [log, errors]
      outputs:
        data:
          type: File[]
          outputSource: download/data
        download_log:
          type: File[]
          outputSource: download/log
        download_err:
          type: File[]
          outputSource: download/errors

        ingest_log:
          type: File
          outputSource: ingest/log
        ingest_err:
          type: File
          outputSource: ingest/errors

        index_log:
          type: File
          outputSource: index/log
        index_err:
          type: File
          outputSource: index/errors

        vacuum_log:
          type: File
          outputSource: vacuum/log
        vacuum_err:
          type: File
          outputSource: vacuum/errors
    out:
      - data
      - download_log
      - download_err
      - ingest_log
      - ingest_err
      - index_log
      - index_err
      - vacuum_log
      - vacuum_err



outputs:
  registry:
    type: File?
    outputSource: registry/model
  registry_log:
    type: File?
    outputSource: registry/log
  registry_err:
    type: File?
    outputSource: registry/errors

  data:
    type:
      type: array
      items:
        type: array
        items: [File]
    outputSource: process/data
  download_log:
    type:
      type: array
      items:
        type: array
        items: [File]
    outputSource: process/download_log
  download_err:
    type:
      type: array
      items:
        type: array
        items: [File]
    outputSource: process/download_err

  ingest_log:
    type: File[]
    outputSource: process/ingest_log
  ingest_err:
    type: File[]
    outputSource: process/ingest_err

  index_log:
    type: File[]
    outputSource: process/index_log
  index_err:
    type: File[]
    outputSource: process/index_err

  vacuum_log:
    type: File[]
    outputSource: process/vacuum_log
  vacuum_err:
    type: File[]
    outputSource: process/vacuum_err
