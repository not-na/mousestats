# `mousestats` - A simple mouse statistics tracking tool

This tool was designed to track how many times each mouse button has been clicked. This
is useful if you want to know how long a specific mouse lasts before exhibiting problems
(e.g. bouncing of buttons).

While there are already some programs that do this, they are usually quite heavy and not
very efficient. Some use a full-blown SQL-based database for storing data about each click,
which massively increases storage requirements and reduces the lifespan of the storage medium.

This script simply internally counts mouse clicks and appends a single line of JSON Data
to a log file once every hour. A new log file is created monthly to make it easier to back
up and process them.

## Requirements

This tool uses `Xlib`, which means that it will only work under X-based linux installs.
If there is demand, I may port this to wayland.

Additionally, Python 3.7 or newer is required. Python 3.6 may also work, but is not
officially supported.

## Installation

Clone this repo to a folder of your choice and enter it:

    $ git clone https://github.com/not-na/mousestats.git
    $ cd mousestats

Next, create a virtualenv to install the requirements into:
    
    $ python3 -mvenv mousestats-py
    $ source mousestats-py/bin/activate
    $ pip install -r requirements.txt

## Starting `mousestats` manually

Once you have installed `mousestats`, you can start it from anywhere by running the
`launch.sh` script:
    
    $ bash launch.sh

You can exit it by pressing Ctrl+C in the terminal window or by killing the process
from your task manager.

## Configuring autostart

Usually, you don't want to have to manually start `mousestats` on every boot. Thus, we
should add it to the user-local autostart.

To do this, use whatever autostart mechanism your distribution provides
(e.g. "Startup Application" on Ubuntu) to launch the `launch.sh` script. Other parameters
should not matter.

## Data storage

By default, statistical data is stored in `~/.local/share/mousestats` in files per-month.

The statistic files follow the JSONL standard, e.g. a single JSON object on a line.
Each line contains up to an hour of data, usually less for the first hour that the script
runs.

On the first mouse click in a new hour, the data of the old hour is written out. If the
tool is killed, it also writes out the data. In rare cases, this may cause multiple data
sets to be present for every hour, if the script is restarted several times in a short timeframe.

Take a look at the produced data files to see the exact format.

## Analytics

Run the script `analyze.py` to show some statistics:
    
    $ python analyze.py

Currently, monthly, yearly and overall sums are shown per-button.
Also, a rough estimate of expected mouse life is given.