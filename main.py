import datetime as dt
import json
import pathlib
import time

import argh
import flask
import humanize
import requests
import tailer

app = flask.Flask(__name__)

irc_home = None

site_header = """
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
<style>
 body, h1, h2, h3, h4, h5, h6 {
  font-family: Arial, Helvetica, sans-serif;
}
#table_id td:nth-child(1)  {white-space: nowrap; color: #999; vertical-align: top;}
a { margin-right: 5px; text-decoration: none }
a.current { font-weight: bold; }
</style>
<title>{{ network_name }}/{{ channel_name }}</title>
</head>

<body>
"""

site_footer = """
</div>
</body>

</html>
"""

view_template = site_header + """
<div class="w3-container">
<h1>ii web frontend</h1>
</div>
<div class="w3-row">
<div class="w3-col s2 w3-light-blue w3-padding">
<h2>Networks</h2>
<p>
{% for network_name_, channel_list in channels.items() %}
<h3>{{ network_name_ }}</h3>
<p style="padding-left: 8px;">
{% for channel_name_ in channel_list %}
{% if network_name == network_name_ and channel_name_ == channel_name %}
<b>{{ channel_name }}</b><br/>
{% else %}
<a href="/chat/{{ irc_dir }}/{{ network_name_ }}/{{ channel_name_|replace("#","$") }}">{{ channel_name_ }}</a><br/>
{% endif %}
{% endfor %}
</p>
{% endfor %}
</p>
</div>
<div class="w3-col s10 w3-light-gray w3-padding">
<p>
<table id="table_id">
{%- for line in lines if line != ("", "") %}
{% set time_str, line_str = ii_line_datefmt(line) %}
<tr>
<td>{{ time_str }}</td>
<td>{{ line_str }}</td>
{% endfor %}
</table>
</p>
<p>
<form method="POST">
<input class="w3-input" type="text" name="user_msg" placeholder="Type message or command here"></input>
</form>
</p>
""" + site_footer


def ii_line_datefmt(line):
    try:
        words = line.split()
        t = humanize.naturaldelta(time.time() - int(words[0]))
        return t, " ".join(words[1:])
    except:
        return "", ""

def get_channels(irc_dir):
    channels = dict()
    networks = [x.name for x in (irc_home / irc_dir).glob("*")]
    for network in networks:
        channels_ = [x.name for x in (irc_home / irc_dir / network).glob("*") if x.name != "in" and x.name != "out"]
        channels[network] = channels_
    return channels


@app.route("/chat/<irc_dir>")
def chat_index(irc_dir):
    channels = get_channels(irc_dir)
    network_name = list(channels.keys())[0]
    channel_name = channels[network_name][0]
    return chat(irc_dir, network_name, channel_name)


@app.route("/chat/<irc_dir>/<network_name>/<channel_name>", methods=["GET", "POST"])
def chat(irc_dir, network_name, channel_name):
    channel_name = channel_name.replace("$", "#")
    channels = get_channels(irc_dir)

    with open(irc_home / irc_dir / network_name / channel_name / "out") as f:
        lines = tailer.tail(f, 25)

    if flask.request.method == "POST":
        user_msg = flask.request.form.get("user_msg")
        print(flask.request.form)
        with open(irc_home / irc_dir / network_name / channel_name / "in", "w") as f:
            f.write(user_msg + "\n")
        return flask.redirect(flask.url_for("chat", irc_dir=irc_dir, network_name=network_name, channel_name=channel_name))
    else:
        return flask.render_template_string(view_template,
                                            irc_dir=irc_dir, network_name=network_name, channel_name=channel_name,
                                            channels=channels,
                                            lines=lines,
                                            ii_line_datefmt=ii_line_datefmt)




def go(irc_home_="/home/ubuntu", port=12345, debug=False):
    global irc_home
    irc_home = pathlib.Path(irc_home_)
    app.run(port=port, debug=debug)

if __name__ == "__main__":
    argh.dispatch_command(go)
