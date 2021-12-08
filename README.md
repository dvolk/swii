# swii - silly web ii

![swii screenshot](https://i.imgur.com/gWAZ7XO.png)

swii is a very simple, no javascript web frontend for ii. If you're not familiar with ii, don't worry. It's an irc client for weirdos.

You need ii installed and at least one instance running and connected to a server. swii can use multiple ii's connected to different servers.

## Install and run

    pip3 install argh flask humanize requests tailer
    python3 main.py --irc_home <dir> --port <port>

Here `dir` is the directory containing your `ii` directories.

For example if you started your ii as `ii -i /home/username/irc` then your irc_home would be `/home/username`

## Public-facing swii

If you want to run swii on a public host, you should configure your web server to use basic authentication.

## Multi-user swii

If you want to run a public multi-user swii with user accounts, you can configure your web server to use different user accounts.

for example

    /chat/username1/*
    /chat/username2/*
    ...

where `username1` and `username2` are ii dirs inside the swii irc_home

sigh.

## FAQ

### Why doesn't the page refresh automatically?

We're keeping it simple. If that's what you want then get a browser extension that does it.

### Why can't I scroll back infinitely?

Buzz off.
