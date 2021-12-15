# swii - silly web IRC interface

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

## Install and run

Install and run `ii`:

    apt install ii
    
Run `ii` and connect to at least one network:

    ii -s irc.libera.chat -n <your_irc_username> -i <irc_dir>

Join at least once channel:

    echo "/j #ubuntu" > <irc_dir>/in

Install `swii` dependencies:

    apt install python3-pip
    pip3 install argh flask humanize waitress

Run `swii`:

    python3 main.py --irc_home <irc_home_dir> --port <port>

Here `irc_home_dir` is the directory containing your `irc_dir` directories. 

For example if launched `ii` with `-i /home/ubuntu/myirc` then `irc_home_dir` is `/home/ubuntu`

Open your browser at 

    http(s)://localhost:<yourport>/chat/<irc_dir>
    
To connect to another network, run another `ii` process with the same `irc_dir`

## Public-facing swii

If you want to run `swii` on a public host, you should configure your web server to use basic authentication.

## Multi-user swii

If you want to run a public multi-user `swii` with user accounts, you can configure your web server to use different user accounts.

for example

    /chat/username1/*
    /chat/username2/*
    ...

where `username1` and `username2` are ii dirs inside the swii `irc_home`

sigh.
