import datetime as dt
import json
import pathlib
import time

import argh
import flask
import humanize

import tail

app = flask.Flask(__name__)

irc_home = None
display_n_messages = None
reload_speed= None

site_header = """
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/w3.css">
<link rel="stylesheet" href="/static/w3-colors-2021.css">
<style>
 body, h1, h2, h3, h4, h5, h6 {
  font-family: Arial, Helvetica, sans-serif;
}
#table_id td:nth-child(1)  {white-space: nowrap; color: #999; vertical-align: top;}
#table_id td:nth-child(2)  {white-space: nowrap; vertical-align: top; text-align:right}
a { margin-right: 5px; text-decoration: none }
a.current { font-weight: bold; }
</style>
<title>{{ network_name }}/{{ channel_name }}</title>
</head>

<body>
"""

site_footer = """
</div>
<script>
{% if reload_page %}
   window.setInterval(function() {
      var msgboxtext = document.getElementById("msgtextbox").value;
      if (!document.hidden && document.getSelection().toString() == "" && msgboxtext == "") {
         window.location.reload(1);
      }
   }, 30000)
{% endif %}
</script>
</body>

</html>
"""

view_template = site_header + """
<div class="w3-container">
<h1>ii web frontend</h1>
</div>
<div class="w3-row">
<div class="w3-col s2 w3-2021-mint w3-padding">
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
  <a href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, skip=skip+25,start=start+25) }}">
    Up 25 messages
  </a>&nbsp;&nbsp;
  <a href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, skip=skip-25, start=start-25) }}">
    Down 25 messages
  </a>&nbsp;&nbsp;
  <a href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name) }}">
    Reset
  </a>&nbsp;&nbsp;
{% if reload_page %}
  <a href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, reload_page=false) }}">Stop reloading</a>
{% endif %}
</p>
<p>
<table id="table_id">
{%- for line in lines if line != ("", "", "") %}
{% set time_str, nick_str, line_str = ii_line_fmt(line) %}
<tr>
<td>{{ time_str }}</td>
{% if nick_str %}
<td>{{ color_nickname(nick_str)|safe }}</td>
{% else %}
<td></td>
{% endif %}
{% if nick_str %}
<td style="padding-left: 5px;">{{ line_str }}</td>
{% else %}
<td style="padding-left: 5px; color: #999">{{ line_str }}</td>
{% endif %}
{% endfor %}
</table>
</p>
<form method="POST">
<p>
<input class="w3-input" id="msgtextbox" type="text" name="user_msg" placeholder="Type message or command here"/>
</p>
</form>
""" + site_footer

colors = ["w3-red", "w3-pink", "w3-purple", "w3-indigo", "w3-light-blue", "w3-cyan", "w3-aqua", "w3-teal", "w3-green", "w3-light-green", "w3-sand", "w3-khaki", "w3-yellow", "w3-amber", "w3-orange", "w3-deep-orange", "w3-blue-gray", "w3-brown", "w3-gray", "w3-dark-gray", "w3-pale-red", "w3-pale-yellow", "w3-pale-green", "w3-pale-blue"]

def color_nickname(nickname):
    color = colors[abs(hash(nickname)) % len(colors)]
    html_str = f"""<span style="padding: 1px;" class="w3-round { color }">{ nickname[1:-1] }</span>"""
    print(color, html_str)
    return html_str


def ii_line_fmt(line):
    try:
        words = line.split()
        t = humanize.naturaldelta(time.time() - int(words[0]))
        if words[1][0] == "<": # nickname
            return t, words[1], " ".join(words[2:])
        else:
            return t, "", " ".join(words[1:])
    except:
        return "", "", ""

def get_channels(irc_dir):
    channels = dict()
    networks = [x.name for x in (irc_home / irc_dir).glob("*")]
    for network in networks:
        channels_ = [x.name for x in (irc_home / irc_dir / network).glob("*") if x.name != "in" and x.name != "out"]
        channels[network] = channels_
    return channels


@app.route("/")
def index():
    flask.abort(404, "Please go to /chat/<irc_dir>, where irc_dir is what you ran ii with. This might be a username or some other identifier")


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
    start = int(flask.request.args.get("start", "25"))
    skip = int(flask.request.args.get("skip", "0"))

    reload_page = False
    if skip == 0 and flask.request.args.get("reload_page") != "False":
        reload_page = True

    with open(irc_home / irc_dir / network_name / channel_name / "out") as f:
        lines = tail.tail(f, start+skip)[skip:start]

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
                                            ii_line_fmt=ii_line_fmt,
                                            color_nickname=color_nickname,
                                            skip=skip, start=start,
                                            reload_page=reload_page)




def go(irc_home_="/home/ubuntu", reload_speed_=30, display_n_messages_=25, port=12345, debug=False):
    global irc_home
    irc_home = pathlib.Path(irc_home_)
    global display_n_messages
    display_n_messages = display_n_messages_
    global reload_speed
    reload_speed =  reload_speed_
    app.run(port=port, debug=debug)

if __name__ == "__main__":
    argh.dispatch_command(go)
