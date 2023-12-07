import curses
import time
import logging
from queue import LifoQueue, Empty


# assuming 128x24 screen
# TODO: resizing support: use KEY_RESIZE
class CurseUI:
    def __init__(self, device_values_to_display: dict[str, LifoQueue], row_templates: dict):
        self.device_values = device_values_to_display
        self.row_templates = row_templates
        self.drawn_rows = {}

    def _draw_loop(self, stdscr):
        while True:
            # TODO: clear queue eventually
            self._draw_once(stdscr)
            time.sleep(1)

    def _draw_once(self, stdscr):
        stdscr.clear()
        # TODO: assuming here
        stdscr.addstr(0, 0, f"{'Running on pi: PI1':128}", curses.A_REVERSE)
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
                old_row = self.drawn_rows.get(key)
                values["timestamp"] = time.strftime('%H:%M:%S', values["timestamp"])
                self.drawn_rows[key] = template.format(**values)
                stdscr.addstr(row, 0, self.drawn_rows[key])
                if old_row != self.drawn_rows[key]:
                    # new data
                    stdscr.addstr(row, 0, self.drawn_rows[key], curses.A_BOLD)
                else:
                    stdscr.addstr(row, 0, self.drawn_rows[key])
        stdscr.refresh()

    def draw_loop(self):
        curses.wrapper(self._draw_loop)
        # while True:
        #     time.sleep(1)
