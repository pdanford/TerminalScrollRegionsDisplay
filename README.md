Terminal Window Scroll Region(s)
--------------------------------------------------------------------------------
This is a python class to manage output to a terminal window in the form of one or more scroll regions.

Each new instance will establish and print lines in a terminal scroll region whose position starts immediately after any previously instantiated scroll region. That is, each region location is based on the number of rows in the region and how many regions have already been created.

pdanford - January 2021

##### Title
Regions can either have a title or not. In the case of no title, regions have no separation. A title of " " can be used in this case to provide separation if desired.

##### Height
Default hight is 8 rows (including any title). This can be changed during region creation.

##### Width
Region width is technically all the way across the terminal window. But visually, it's whatever the title and lines added appear to be.

##### Scroll Delay
Note that by default there is a small delay after each line is added to allow some readability to regions being updated very fast. This can be set to zero in the AddLine() call if undesirable. Conversely, don't set too large because it's blocking.

##### Regarding Terminal Window Size
There is no terminal window size change callback, so instead any scroll region refresh happens when a new line is added through AddLine().

If the terminal window height is not enough to display scroll regions for all scroll region instances, a highlighted ↓ will appear in the first column which means "more scroll regions hidden below". When window height is increased, these are cleared/updated during the next AddLine() call.

### Use
See [example](example.py).

### Requirements
- Python 3.6+ 
- Terminal with VT100 escape sequence compatibility (e.g. macOS terminal, iTerm2)

---
:scroll: [MIT License](README.license)

