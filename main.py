import collections
import datetime as dt
import json
import pathlib
import time

import argh
import flask
import humanize
import waitress

import tail

app = flask.Flask(__name__)

irc_home = None
display_n_messages = None
reload_speed = None


last_viewed_timestamp = collections.defaultdict(int)


with open("static/w3.css") as f:
    css = f.read()


site_header = """
<html>
  <head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel='shortcut icon' type='image/x-icon' href='/static/favicon.ico'/>
    <style>
{{ css }}
      body, h1, h2, h3, h4, h5, h6 {
      font-family: Arial, Helvetica, sans-serif;
      }
      #table_id td:nth-child(1)  {white-space: nowrap; color: #999; vertical-align: top;}
      #table_id td:nth-child(2)  {white-space: nowrap; vertical-align: top; text-align:right}
      a { margin-right: 5px; text-decoration: none }
      a.current { font-weight: bold; }
      td a { color: revert; text-decoration: revert }
      span.line a { color: revert; text-decoration: revert }
    </style>
    <title>{{ channel_name }} @ {{ network_name }}</title>
  </head>
  <body>
"""

site_footer = """
</div>
<script>
  var last_focused = 0;
  {% if reload_page %}
    window.setInterval(function() {
    /* Don't reload if:
    1. The page is hidden
    2. Any text is selected on the page
    3. The message text box is in focus
    */
    var dt =  Date.now() - last_focused;
    var should_reload_page = !document.hidden &&
                              document.getSelection().toString() == "" &&
                              document.activeElement.id != "msgtextbox" &&
                              dt > {{ reload_speed*100 }};
    if (should_reload_page) {
        window.location.reload(1);
        last_focused = Date.now();
    }
    else {
        document.getElementById("reload_status").innerHTML = "Reloading paused"
    }
    }, {{ reload_speed*1000 }})
    document.addEventListener( 'visibilitychange' , function() {
        var dt =  Date.now() - last_focused;
        console.log(dt);
        if (document.hidden) {
            last_focused = Date.now();
            console.log('bye');
        } else {
            if(dt > {{ reload_speed*100 }}) {
                 window.location.reload(1);
            }
            console.log('well back');
        }
    }, false );
  {% endif %}
</script>
</body>
</html>
"""
view_template = (
    site_header
    + """
<br/>
{% if not phone_mode %}
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
            <a class="menu" href="{{ url_for('chat', irc_dir=irc_dir, network_name=network_name_, channel_name=channel_name_|replace('#','$'), start=start, phone=phone, show_events=show_events) }}">{{ channel_name_ }}</a><br/>
          {% endif %}
        {% endfor %}
      </p>
    {% endfor %}
      </p>
    </div>
  {% endif %}
  {% if phone_mode %}
    <div class="w3-col w3-light-gray">
  {% else %}
    <div class="w3-col w3-light-gray s10 w3-padding">
  {% endif %}
  <p>
    <a class="menu" href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, skip=skip+25,start=start+25) }}">
      Up 25 messages
    </a>&nbsp;&nbsp;
    <a class="menu" href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, skip=skip-25, start=start-25) }}">
      Down 25 messages
    </a>&nbsp;&nbsp;
    <a class="menu" href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name) }}">
      Reset
    </a>&nbsp;&nbsp;
    {% if reload_page %}
      <a class="menu" href="{{url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, reload_page=false) }}">Stop reloading</a>&nbsp;&nbsp;
    {% endif %}
    <span id="reload_status">Reload active</span>&nbsp;&nbsp;
    <a class="menu" href="{{ url_for('chat', irc_dir=irc_dir, network_name=network_name, channel_name=channel_name, phone=(not phone_mode)) }}">Phone mode</a>
  </p>
  <p>
    {% if not phone_mode %}
      <table width=100% id="table_id">
        {%- for line in lines if line != ("", "", "", "") %}
          {% set epoch_time, time_str, nick_str, line_str = line %}
          <tr style="">
            <td>{{ time_str }}</td>
            {% if nick_str %}
              <td>{{ color_nickname(nick_str)|safe }}</td>
            {% else %}
              <td></td>
            {% endif %}
            {% if nick_str %}
              <td width="99%" style="{% if epoch_time == ctx_last_viewed_timestamp %}border-bottom: 2px dashed red;{% endif %}">{{ line_str|safe }}</td>
            {% else %}
              <td width="99%" style="{% if epoch_time == ctx_last_viewed_timestamp %}border-bottom: 2px dashed red;{% endif %}color: #999">{{ line_str|safe }}</td>
            {% endif %}
          {% endfor %}
      </table>
    {% endif %}
    {% if phone_mode %}
      {% for line in lines if line != ("", "", "", "") %}
        {% set epoch_time, time_str, nick_str, line_str = line %}
        {% if nick_str %}
          <span class="line" style="{% if epoch_time == ctx_last_viewed_timestamp %}border-bottom: 2px dashed red;{% endif %}">{{ color_nickname(nick_str)|safe }} {{ line_str|safe }}<br/></span>
        {% else %}
          <span class="line" style="{% if epoch_time == ctx_last_viewed_timestamp %}border-bottom: 2px dashed red;{% endif %} padding-left: 5px; color: #999">{{ line_str|safe }}</span><br/>
        {% endif %}
      {% endfor %}
    {% endif %}
  </p>
  <form method="POST">
    <p>
      <input class="w3-input" id="msgtextbox" type="text" name="user_msg" placeholder="Type message or command here"/>
    </p>
  </form>
"""
    + site_footer
)

nick_colors = [
    "w3-amber",
    "w3-aqua",
    "w3-blue",
    "w3-light-blue",
    "w3-brown",
    "w3-cyan",
    "w3-blue-grey",
    "w3-green",
    "w3-light-green",
    "w3-indigo",
    "w3-khaki",
    "w3-lime",
    "w3-orange",
    "w3-deep-orange",
    "w3-pink",
    "w3-purple",
    "w3-deep-purple",
    "w3-red",
    "w3-sand",
    "w3-teal",
    "w3-yellow",
    "w3-pale-red",
    "w3-pale-green",
    "w3-pale-yellow",
    "w3-pale-blue",
]


def color_nickname(nickname):
    color = nick_colors[abs(hash(nickname)) % len(nick_colors)]
    html_str = f"""<span style="padding: 1px;" class="w3-round { color }">{ nickname[1:-1] }</span>"""
    return html_str


def save_last_viewed_timestamp(lines, irc_dir, network_name, channel_name):
    global last_viewed_timestamp
    print(last_viewed_timestamp)
    for words in reversed(lines):
        try:
            timestamp = int(words[0])
            last_viewed_timestamp[
                f"{irc_dir}${network_name}${channel_name}"
            ] = timestamp
            return
        except:
            pass


def get_channels(irc_dir):
    channels = dict()
    networks = [x.name for x in (irc_home / irc_dir).glob("*")]
    for network in networks:
        channels__ = sorted((irc_home / irc_dir / network).glob("*"))
        channels_ = [
            x.name
            for x in channels__
            if x.name != "in" and x.name != "out" and (x / "out").is_file()
        ]
        channels[network] = channels_
    return channels


@app.route("/")
def index():
    flask.abort(
        404,
        "Please go to /chat/<irc_dir>, where irc_dir is what you ran ii with. This might be a username or some other identifier",
    )


@app.route("/chat/<irc_dir>")
def chat_index(irc_dir):
    channels = get_channels(irc_dir)
    network_name = list(channels.keys())[0]
    channel_name = channels[network_name][0]
    return chat(irc_dir, network_name, channel_name)


@app.route("/chat/<irc_dir>/<network_name>/<channel_name>", methods=["GET", "POST"])
def chat(irc_dir, network_name, channel_name):
    global last_viewed_timestamp
    channel_name = channel_name.replace("$", "#")
    channels = get_channels(irc_dir)
    start = int(flask.request.args.get("start", "25"))
    skip = int(flask.request.args.get("skip", "0"))
    phone_mode = bool(flask.request.args.get("phone") == "True")
    show_events = bool(flask.request.args.get("show_events") == "True")

    reload_page = False
    if skip == 0 and flask.request.args.get("reload_page") != "False":
        reload_page = True

    if show_events:
        with open(
            irc_home / irc_dir / network_name / channel_name / "out", errors="ignore"
        ) as f:
            lines = tail.tail(f, start + skip)[skip:start]
    else:
        with open(
            irc_home / irc_dir / network_name / channel_name / "out", errors="ignore"
        ) as f:
            lines = tail.chat_only_tail(f, start + skip)[skip:start]

    ctx_hash = f"{irc_dir}${network_name}${channel_name}"
    ctx_last_viewed_timestamp = last_viewed_timestamp[ctx_hash]
    save_last_viewed_timestamp(lines, irc_dir, network_name, channel_name)
    print(ctx_last_viewed_timestamp)
    if ctx_last_viewed_timestamp == last_viewed_timestamp[ctx_hash]:
        ctx_last_viewed_timestamp = 0

    if flask.request.method == "POST":
        user_msg = flask.request.form.get("user_msg")
        print(flask.request.form)
        with open(irc_home / irc_dir / network_name / channel_name / "in", "w") as f:
            f.write(user_msg + "\n")
        return flask.redirect(
            flask.url_for(
                "chat",
                irc_dir=irc_dir,
                network_name=network_name,
                channel_name=channel_name,
            )
        )
    else:
        return flask.render_template_string(
            view_template,
            irc_dir=irc_dir,
            css=css,
            network_name=network_name,
            channel_name=channel_name,
            channels=channels,
            lines=lines,
            color_nickname=color_nickname,
            skip=skip,
            start=start,
            reload_page=reload_page,
            reload_speed=reload_speed,
            ctx_last_viewed_timestamp=ctx_last_viewed_timestamp,
            phone_mode=phone_mode,
        )


def go(
    irc_home_="/home/ubuntu",
    reload_speed_=30,
    display_n_messages_=25,
    port=12345,
    debug=False,
):
    global irc_home
    irc_home = pathlib.Path(irc_home_)
    global display_n_messages
    display_n_messages = display_n_messages_
    global reload_speed
    reload_speed = reload_speed_
    if debug:
        app.run(port=port, debug=True)
    else:
        waitress.serve(app, port=port)


if __name__ == "__main__":
    argh.dispatch_command(go)
