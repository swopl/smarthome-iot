import curses


# assuming 128x24 screen
# TODO: resizing support: use KEY_RESIZE
class CurseUI:
    def __init__(self):
        pass

    def _draw_loop(self, stdscr):
        stdscr.clear()
        # This raises ZeroDivisionError when i == 10.
        for i in range(0, 9):
            v = i-10
            stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))
        stdscr.refresh()
        key = stdscr.getkey()

    def draw_loop(self):
        curses.wrapper(self._draw_loop)
