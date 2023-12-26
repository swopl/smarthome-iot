import curses
import logging
import time
from datetime import datetime
from queue import LifoQueue, Empty
from collections import defaultdict


# assuming 128x24 screen
# TODO: resizing support: use KEY_RESIZE
def _dialog_read_line(stdscr, msg):
    # TODO: check if staying in the dialog somehow breaks anything
    rows, cols = stdscr.getmaxyx()
    dialog = curses.newwin(4, 40, 4, 8)
    dialog.border(0)
    dialog.addstr(0, 2, msg)
    curses.echo()
    dialog.addstr(1, 1, ">>")
    ret = dialog.getstr(1, 4, 3)
    curses.noecho()
    return ret


def _dialog_read_rgb_color(stdscr, msg):
    # TODO: handle bad input
    return tuple(int(chr(num)) for num in _dialog_read_line(stdscr, msg))


class CurseUI:

    def do_quit(self):
        raise KeyboardInterrupt

    # TODO: move out of this class somewhere better. Components should decide their own commands
    key_to_cmd = {"Q": (None, do_quit),
                  "J": ("DL", False),
                  "O": ("DL", True),
                  "B": ("DB", {"pitch": 440, "duration": 0.3}),
                  "R": ("BRGB", None)}
    key_to_descr = {"Q": "Quit",
                    "J": "Turn Door Light off",
                    "O": "Turn Door Light on",
                    "B": "Buzz the buzzer",
                    "R": "Set RGB color"}

    def __init__(self, device_values_to_display: dict[str, LifoQueue], row_templates: dict,
                 command_queues: dict[str, LifoQueue]):
        self.device_values = device_values_to_display
        self.row_templates = row_templates
        self.command_queues = command_queues
        self.drawn_rows = {}
        # FIXME: check if this works same on all python versions
        self.latest_times = defaultdict(lambda: datetime.min)

    def _draw_loop(self, stdscr):
        curses.curs_set(0)
        # will make getkey block for 600ms. FIXME: this might very rarely cause dropped inputs
        stdscr.timeout(600)
        while True:
            # TODO: clear queue eventually
            self._draw_once(stdscr)  # this should contain some sleeps inside, or blocking

    def _draw_help(self, stdscr):
        rows, _ = stdscr.getmaxyx()
        line = rows-1
        for keypress, help_text in self.key_to_descr.items():
            stdscr.addstr(line, 0, f"{keypress}: {help_text}", curses.A_ITALIC)
            line -= 1

    def _draw_once(self, stdscr):
        try:
            keypress = stdscr.getkey()
        except curses.error:
            keypress = None
        if keypress and keypress.upper() in self.key_to_cmd:
            component, command = self.key_to_cmd[keypress.upper()]
            if not component:
                command(self)
            else:
                if command is None:
                    command = _dialog_read_rgb_color(stdscr, "Enter rgb color")
                self.command_queues[component].put(command)
            time.sleep(0.08)  # just in case to match ui faster FIXME: might not need it
        stdscr.clear()
        # TODO: assuming here
        stdscr.addstr(0, 0, f"{'Running on pi: PI1':128}", curses.A_REVERSE)
        self._draw_help(stdscr)
        for key in self.device_values:
            row, template = self.row_templates[key]
            queue = self.device_values[key]
            try:
                values = queue.get(timeout=0.01).copy()
            except Empty:
                if key not in self.drawn_rows:
                    stdscr.addstr(row, 0, f"No data yet from {key}")
                else:
                    stdscr.addstr(row, 0, self.drawn_rows[key])
                continue
            else:
                t = values["timestamp"]
                if self.latest_times[key] < t:
                    # new data
                    values["timestamp"] = t.strftime('%H:%M:%S.%f')[:-3]
                    self.drawn_rows[key] = template.format(**values)
                    self.latest_times[key] = t
                    stdscr.addstr(row, 0, self.drawn_rows[key], curses.A_BOLD)
                else:
                    stdscr.addstr(row, 0, self.drawn_rows[key])
        stdscr.refresh()

    def draw_loop(self):
        try:
            curses.wrapper(self._draw_loop)
        except curses.error:
            print("Curses failed! Is your terminal big enough? Exiting...")
            raise KeyboardInterrupt
