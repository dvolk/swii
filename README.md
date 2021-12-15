# swii - simple web IRC interface

![workflow](https://github.com/dvolk/swii/actions/workflows/test_swii.yml/badge.svg)

`swii` is a simple Python web IRC client.

# Screenshot

![swii screenshot](https://i.imgur.com/uMhkNho.png)

# Features

* No javascript required
* Multi-user support
* Multi-network per-user support
* Uses `ii` for handling IRC protocol
* optional javascript enhancement to refresh page on page focus/turn off refresh when text is selected or text written to message box
* Humanized timestamps
* Shows only chat by default, other noisy IRC events are hidden
* URLs truncated to hostnames
* Colorful nicknames
* dashed horizontal line shows lines since last refresh
* Compact phone mode
* ~300 lines of Python 3 + html template

## Install and run on Ubuntu

### Install and run `ii`

    apt install ii
    
Run `ii` and connect to at least one network (`irc_dir` is whatever you want, eg `/home/ubuntu/myirc`):

    ii -s irc.libera.chat -n <your_irc_username> -i <irc_dir>

Join at least once channel:

    echo "/j #ubuntu" > <irc_dir>/in

#### Connecting to another network

To connect to another network, run another `ii` process with the same `irc_dir`

### Install and run `swii`

Install Python 3 and pip package manager:

    apt install python3-pip

Install `swii` Python 3 dependencies:

    pip3 install argh flask humanize waitress

Run `swii`:

    python3 main.py --irc_home <irc_home_dir> --port <port>

Here `irc_home_dir` is the directory containing your `irc_dir` directories. 

For example if launched `ii` with `-i /home/ubuntu/myirc` then `irc_home_dir` is `/home/ubuntu`

### Browse to `swii` URL in browser:

    http(s)://localhost:12345/chat/<irc_dir>

## Public-facing swii

If you want to run `swii` on a public host, you should configure your web server to use basic authentication.

## Multi-user swii

If you want to run a public multi-user `swii` with user accounts, you can configure your web server to use different user credentials for different `irc_dir`s:

for example:

    /chat/username1/*
    /chat/username2/*
    ...

where `username1` and `username2` are `ii` dirs inside the swii `irc_home`
