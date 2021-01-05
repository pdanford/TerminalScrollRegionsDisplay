#!/usr/bin/env python3
# requires Python 3.6+ 

# pdanford - January 2021
# MIT License

"""
Example use of ScrollRegion to display 3 regions.
"""

import random
from ScrollRegion import ScrollRegion

region_width=20
ansi_green_bg = "\x1b[42m"
ansi_reset = "\x1b[0m"

# create 3 scroll regions
region_list = []
for i in range(1,4):
    name = f"Region {i}"
    title = f"{ansi_green_bg}{name:^{region_width}}{ansi_reset}"
    region_list.append(ScrollRegion(title))

try:
    # add lines to the regions at different rates
    for i in range(10000):
        line = f"{i:-^{region_width}}"
        random.choices(region_list, weights=(0.30,0.10,0.60))[0].AddLine(line)

except KeyboardInterrupt:
    # Suppress python error when <ctrl><c> is used to exit
    pass
