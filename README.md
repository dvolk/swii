# swii - silly web IRC interface

![swii screenshot](https://i.imgur.com/KbDq9OK.png)

`swii` is a very simple, no-javascript[*] web client for IRC. It uses `ii` to handle the irc protocol (https://tools.suckless.org/ii/)

You need `ii` installed and at least one instance running and connected to a server (see above url for instructions). 

`swii` can use multiple ii's connected to different servers.

[*] a tiny bit of javascript is used to refresh the page periodically, and to stop refreshing if any text is selected on the page or the user writes anything in the message box. However this is optional. You can disable javascript and manually refresh the page or use a browser extension.

## Install and run

Install and run `ii`

Install `swii` dependencies:

    pip3 install argh flask humanize

Run `swii`:

    python3 main.py --irc_home <dir> --port <port>

Here `dir` is the directory containing your `ii` directories.

For example if you started your ii as `ii -i /home/username/irc` then your `irc_home` would be `/home/username`

Open your browser at `http(s)://localhost:<yourport>/chat/<dir>`
    
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
