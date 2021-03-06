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

import csv
import gzip
import os
import sys


if __name__ == '__main__':
    f1 = sys.argv[1]
    c1 = int(sys.argv[2]) - 1
    f2 = sys.argv[3]
    c2 = int(sys.argv[4]) - 1

    print("{}:{:d} - {}:{:d}".format(f1, c1, f2, c2))

    n = 0
    codes = set()
    with (gzip.open(f2, "rt")) as s:
        reader = csv.reader(s)
        #next(reader)
        for row in reader:
            codes.add(int(row[c2]))
            n += 1
            if (n % 10000000) == 0:
                print("{:d} codes from {:,} lines".format(len(codes), n))

    f4 = os.path.join(os.path.dirname(f2), "codes_" + os.path.basename(f2))
    with (gzip.open(f4, "wt")) as writer:
        writer.writelines([str(code) for code in codes])

    print("Set created: {:d} codes from {:,} lines".format(len(codes), n))
    n = 0
    m = 0
    f3 = os.path.join(os.path.dirname(f1), "__" + os.path.basename(f1))
    with (gzip.open(f1, "rt")) as reader, (gzip.open(f3, "wt")) as writer:
        writer.write(next(reader))
        for line in reader:
            n += 1
            data = line.split(',')
            try:
                code = int(data[c1])
            except Exception as x:
                print(x)
                code = data[c1]
            if code not in codes:
                writer.write(line)
                m += 1
            if (n % 100000) == 0:
                print("{:d} / {:d}".format(n, m))
    print("All done: {:d} / {:d}".format(n, m))