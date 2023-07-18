#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  main.py
#
#  Copyright 2022 notna <notna@apparat.org>
#
#  This file is part of mousestats.
#
#  mousestats is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  mousestats is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mousestats.  If not, see <http://www.gnu.org/licenses/>.
#

# Roughly based on https://github.com/MBaltz/kbdcounter/blob/master/src/kbdcounter.py

import os
import optparse
import signal
import sys
import time
import threading
from datetime import datetime
import json

import xlib


class MouseCounter:
    def __init__(self, options):
        self.datapath = os.path.expanduser(options.datapath)

        self.running = True

        self.counts = {"BTN_LEFT": 0}

        self.last_save = datetime.now()

    def handle_event(self, event):
        if event.type == "EV_KEY" and event.scancode == 0:
            self.handle_mouse_button(event)

    def handle_mouse_button(self, event):
        # updown = "up" if event.value == 0 else "down"
        # print(f"[MOUSE] {event.type} Button {event.code} went {updown}")

        self.check_save()

        if event.value == 1:
            if event.code not in self.counts:
                self.counts[event.code] = 0
            self.counts[event.code] += 1

            # print(f"Counts: {self.counts}")

    def check_save(self):
        now = datetime.now()

        if now.date() != self.last_save.date() or now.hour != self.last_save.hour:
            self.save()

    def save(self):
        data = self.counts
        self.counts = {"BTN_LEFT": 0}

        data["time"] = self.last_save.strftime("%d.%m.%Y %H:%M:%S")
        dat = json.dumps(data)

        fname = os.path.join(self.datapath, f"data_{self.last_save:%Y_%m}.jsonl")

        os.makedirs(os.path.dirname(fname), exist_ok=True)

        with open(fname, "a") as f:
            f.write(dat + "\n")

        print(f"Saved! data='{dat}'")

        self.last_save = datetime.now()

    def sig_handler(self, signum, frame):
        print(f"Received signal {signum}, saving and exiting")
        self.save()
        self.running = False

        sys.exit()

    def run(self):
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGHUP, self.sig_handler)

        events = xlib.XEvents()

        event_ready = threading.Event()
        events.set_event(event_ready)

        events.start()

        # Wait for init
        while not events.listening():
            time.sleep(0.1)

        try:
            print("mousestats started")

            while self.running:
                event = events.next_event()
                while event:
                    self.handle_event(event)
                    event = events.next_event()

                event_ready.clear()
                event_ready.wait()
        except KeyboardInterrupt:
            self.save()
        finally:
            print("mousestats stopping")
            events.stop_listening()


def main():
    oparser = optparse.OptionParser()
    oparser.add_option(
        "--datapath",
        dest="datapath",
        help="Base data directory for storing statistics",
        default="~/.local/share/mousestats/",
    )

    options, args = oparser.parse_args()

    counter = MouseCounter(options)
    counter.run()


if __name__ == "__main__":
    main()
