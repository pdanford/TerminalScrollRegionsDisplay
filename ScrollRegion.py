from time import sleep
from shutil import get_terminal_size
from collections import deque

# version 1.0.0
# requires Python 3.6+ 
# pdanford - January 2021
# MIT License

class ScrollRegion:
    """
    Establish and print lines in a terminal scroll region.
    Each region location is based on the number of rows in the region and 
    how many regions have already been created.

    Note: requires VT100 escape compatibility
    """

    ## ----- class values -----

    # where 1st instance scroll region is located in terminal window
    __scroll_region_start_row = 1

    # used to detect terminal window size changes
    __prev_terminal_columns, __prev_terminal_rows = get_terminal_size()

    # a list of all ScrollRegion instances
    __scroll_regions_list = []

    ## ----- instance variables -----

    # storage for scroll region title line 
    # note this should only be updated after creation through SetTitle()
    # because it modifies the scroll region start location
    # (takes up 1 row of scroll_region_height)
    __title = ""

    # storage for last row number of terminal scroll region
    __scroll_region_end_row = 0

    # small cache for the lines added to the region
    __line_cache = deque()


    def __init__(self,
                 title = "",
                 scroll_region_height = 8):
        """
                       title - if not "", takes up 1 row of scroll_region_height
        scroll_region_height - total height of region (including any title line)
        """
        if scroll_region_height < 2 and title != "":
            raise ValueError\
              ("ScrollRegion: with title, scroll_region_height must be >= 2")
            # technically, VT100 compatibility requires at a scroll height of
            # at least 2 lines, but modern terminal emulators seem to be fine
            # with 1 (which might be useful to some)
        elif scroll_region_height < 1:
            raise ValueError\
              ("ScrollRegion: without title, scroll_region_height must be >= 1")
            # technically, VT100 compatibility requires at a scroll height of
            # at least 2 lines, but modern terminal emulators seem to be fine
            # with 1 (which might be useful to some)

        # instance member initializations
        self.__scroll_region_height = scroll_region_height
        self.__scroll_region_start_row = ScrollRegion.__scroll_region_start_row
        self.__scroll_region_end_row   = (self.__scroll_region_start_row
                                          + scroll_region_height
                                          - 1)
        self.__line_cache = deque()

        # update class global for next new ScrollRegion instantiated
        ScrollRegion.__scroll_region_start_row = self.__scroll_region_end_row + 1

        # prep terminal window on first use for clean display of ScrollRegion(s)
        if len(ScrollRegion.__scroll_regions_list) == 0:
            # clear terminal window scroll-back buffer, otherwise it will
            # interfere with display when terminal window is resized or
            # scrolled back:
            print("\x1bc", end="")   # clear screen
            print("\x1b[3J", end="") # erase terminal scroll-back buffer

        ScrollRegion.__scroll_regions_list.append(self)

        self.ClearScrollRegion("-")

        self.SetTitle(title)


    def __del__(self):
        # print done/exit message (once using __scroll_region_start_row to
        # detect when the oldest ScrollRegion is garbage collected)
        if self.__scroll_region_start_row <= 2:
            print(f"\x1b[r", end="")         # reset term to default scrolling region
            columns, rows = get_terminal_size()
            print(f"\x1b[{rows};1H", end="") # position cursor to window bottom
            print("\n-- done --")


    def ClearScrollRegion(self, blanking_string = ""):
        """
        Blanks the entire scroll region and line cache (including title
        area) with blanking_string.
        """
        # remove any title so entire scroll region is cleared
        self.SetTitle("")

        # flush line cache
        for i in range(self.__scroll_region_height):
            self.AddLine(blanking_string, 0)


    def SetTitle(self, title):
        """
        Sets scroll region title and adjusts start/end rows and prints based on
        whether a title exists or not. If "", then, scroll regions will butt up
        against each other. So use a " " if no title is wanted but still a line
        between regions is desired.
        """
        if self.__title == "":
            if title != "":
                # don't include title in scrolling region
                self.__scroll_region_start_row += 1
        else:
            if title == "":
                # reclaim row previously used for title in scrolling region
                self.__scroll_region_start_row -= 1

        self.__title = title

        # print title for this scrolling region
        if self.__title != "":
            # make sure that this scroll region start is actually on screen
            # and print title at top of scroll region if so
            title_row = self.__scroll_region_start_row - 1
            terminal_columns, terminal_rows = get_terminal_size()
            if (title_row <= terminal_rows and
               title_row > 0):
                print(f"\x1b[{title_row};1H", end="") # position to title row
                print(f"{self.__title}", end="")      # print title
                print("\x1b[K", end="")               # clear rest of line


    def AddLine(self, line, scroll_delay_s = 0.125):
        """
        Add line string to this scroll region.

        scroll_delay_s - scroll delay each line print for readability
        """
        # Add this line to the cache in case its needed for a refresh trigger
        self.__line_cache.append(line)

        if len(self.__line_cache) > self.__scroll_region_height:
            # keep __line_cache length the same as the scroll region height
            self.__line_cache.popleft()

        # Print newly added line to this scroll region end row
        self.__Print(line, scroll_delay_s)

        trigger = self.__CheckScreenRefreshTrigger()
        if trigger == "REPRINT_ALL_SCROLL_REGIONS":
            # entire terminal window needs updating

            # erase terminal scroll-back buffer
            print("\x1b[3J", end="")

            # reprint all regions' cache
            for r in reversed(ScrollRegion.__scroll_regions_list):
                r.__ReprintScrollRegion()


    def __Print(self, line, scroll_delay_s):
        """
        Internal function to print line string  at the last line of this
        instance's scroll region in the terminal window and scroll up one line.

                  line - string to print at bottom of this scroll region
        scroll_delay_s - scroll delay each line print for readability
        """
        # make sure that this scroll region start is actually on screen
        terminal_columns, terminal_rows = get_terminal_size()

        # don't print line if none of scroll region is within terminal window
        if self.__scroll_region_start_row > terminal_rows:
            # there was no room to print in this region
            return

        # ensure area where line data is to be printed is in terminal window
        if self.__scroll_region_end_row > terminal_rows:
            # limit if there's only enough room for partial scroll region
            # (scroll region is truncated) but enough to print line
            print_row_num = terminal_rows
        else:
            print_row_num = self.__scroll_region_end_row

        # set scrolling region for this ScrollRegion instance
        print(f"\x1b[{self.__scroll_region_start_row};{print_row_num}r", end="")
        # position to end of scroll region before printing line data
        print(f"\x1b[{print_row_num};1H", end="")

        if print_row_num - self.__scroll_region_start_row >= 1:
            # prepend a newline to cause previous lines to scroll up in region
            print(f"\n{line}\r", end="")
        else:
            # don't do the prepend \n for scroll regions of 1 row because some
            # terminals will scroll any title line too in certain edge cases
            print(f"{line}\r", end="")


        # scroll delay each line for readability
        sleep(scroll_delay_s)

        return


    def __ReprintScrollRegion(self):
        """
        Internal function used to cause a reprint of this ScrollRegion
        instance's entire line cache and title (if any).
        """
        # reprint title (if any)
        self.SetTitle(self.__title)

        # reprint entire line cache to refresh whole scroll region
        for line in self.__line_cache:
            self.__Print(line, 0)


    def __CheckScreenRefreshTrigger(self):
        """
        Internal function to check if a window resize event happened that
        results in the currently displayed scroll regions being corrupted.
        Some resize changes result in the scroll regions being displayed on
        new window coordinates which don't match previously displayed scroll
        region location because of scroll-back.

        If so, indicate a terminal window buffer reset and reprint of all
        regions' cache is necessary so scroll region coordinates are correct
        for this new terminal window size

        return flag strings:

                      empty string - no reprint necessary
        REPRINT_ALL_SCROLL_REGIONS - window height has changed in such a way
                                     that its scroll-back buffer should be
                                     cleared and all scroll regions should be
                                     reprinted entirely to fix coordinates
        """
        # get current terminal window dimensions
        terminal_columns, terminal_rows = get_terminal_size()

        # assume a scroll region reprint trigger did not happen
        return_flag = ""

        if terminal_rows != ScrollRegion.__prev_terminal_rows:
            # terminal_rows changed which may cause the terminal's scroll-back
            # buffer to activate which causes the scroll region coordinates to
            # change
            return_flag = "REPRINT_ALL_SCROLL_REGIONS"

        elif terminal_columns != ScrollRegion.__prev_terminal_columns:
            # terminal_columns changed which may cause the terminal's
            # scroll-back buffer to activate because of line wrapping
            # which causes the scroll region coordinates to change
            return_flag = "REPRINT_ALL_SCROLL_REGIONS"

        # update for next trigger check
        ScrollRegion.__prev_terminal_columns,\
             ScrollRegion.__prev_terminal_rows = terminal_columns, terminal_rows

        return return_flag

