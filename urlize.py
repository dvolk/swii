# from jinja2
# https://github.com/pallets/jinja/blob/main/src/jinja2/utils.py
# copyright jinja2 authors

import typing as t
import re
import markupsafe
import urllib.parse

_http_re = re.compile(
    r"""
    ^
    (
        (https?://|www\.)  # scheme or www
        (([\w%-]+\.)+)?  # subdomain
        (
            [a-z]{2,63}  # basic tld
        |
            xn--[\w%]{2,59}  # idna tld
        )
    |
        ([\w%-]{2,63}\.)+  # basic domain
        (com|net|int|edu|gov|org|info|mil)  # basic tld
    |
        (https?://)  # scheme
        (
            (([\d]{1,3})(\.[\d]{1,3}){3})  # IPv4
        |
            (\[([\da-f]{0,4}:){2}([\da-f]{0,4}:?){1,6}])  # IPv6
        )
    )
    (?::[\d]{1,5})?  # port
    (?:[/?#]\S*)?  # path, query, and fragment
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)
_email_re = re.compile(r"^\S+@\w[\w.-]*\.\w+$")

colors = [
    "w3-2021-marigold",
    "w3-2021-cerulean",
    "w3-2021-rust",
    "w3-2021-illuminating",
    "w3-2021-french-blue",
    "w3-2021-green-ash",
    "w3-2021-burnt-coral",
    "w3-2021-mint",
    "w3-2021-amethyst-orchid",
    "w3-2021-raspberry-sorbet",
    "w3-2021-inkwell",
    "w3-2021-ultimate-gray",
    "w3-2021-buttercream",
    "w3-2021-desert-mist",
    "w3-2021-willow",
    "w3-2020-classic-blue",
    "w3-2020-flame-scarlet",
    "w3-2020-saffron",
    "w3-2020-biscay-green",
    "w3-2020-chive",
    "w3-2020-faded-denim",
    "w3-2020-orange-peel",
    "w3-2020-mosaic-blue",
    "w3-2020-sunlight",
    "w3-2020-coral-pink",
    "w3-2020-cinnamon-stick",
    "w3-2020-grape-compote",
    "w3-2020-lark",
    "w3-2020-navy-blazer",
    "w3-2020-brilliant-white",
    "w3-2020-ash",
    "w3-2020-amberglow",
    "w3-2020-samba",
    "w3-2020-sandstone",
    "w3-2020-green-sheen",
    "w3-2020-rose-tan",
    "w3-2020-ultramarine-green",
    "w3-2020-fired-brick",
    "w3-2020-peach-nougat",
    "w3-2020-magenta-purple",
]


def colorize_irc2html(line):
    in_bold = False
    in_color = False
    line_ = list(line)
    for i, ch in enumerate(line):
        if ch == "\x02":
            if in_bold:
                in_bold = False
                line_[i] = "</b>"
            else:
                in_bold = True
                line_[i] = "<b>"
        if ch == "\x03":
            if in_color:
                in_color = False
                line_[i] = "</span>"
            else:
                if line[i + 2].isdigit():
                    color = int(line[i + 1] + line[i + 2])
                    if color > len(color):
                        color = int(line[i + 1])
                    line_[i + 1] = ""
                    line_[i + 2] = ""
                else:
                    line_[i + 1] = ""
                    color = int(line[i + 1])
                line_[i] = f'<span class="{ colors[color] }">'
                in_color = True
    return "".join(line_)


def urlize(
    text: str,
    trim_url_limit: t.Optional[int] = None,
    rel: t.Optional[str] = None,
    target: t.Optional[str] = None,
    extra_schemes: t.Optional[t.Iterable[str]] = None,
) -> str:
    """Convert URLs in text into clickable links.
    This may not recognize links in some situations. Usually, a more
    comprehensive formatter, such as a Markdown library, is a better
    choice.
    Works on ``http://``, ``https://``, ``www.``, ``mailto:``, and email
    addresses. Links with trailing punctuation (periods, commas, closing
    parentheses) and leading punctuation (opening parentheses) are
    recognized excluding the punctuation. Email addresses that include
    header fields are not recognized (for example,
    ``mailto:address@example.com?cc=copy@example.com``).
    :param text: Original text containing URLs to link.
    :param trim_url_limit: Shorten displayed URL values to this length.
    :param target: Add the ``target`` attribute to links.
    :param rel: Add the ``rel`` attribute to links.
    :param extra_schemes: Recognize URLs that start with these schemes
        in addition to the default behavior.
    .. versionchanged:: 3.0
        The ``extra_schemes`` parameter was added.
    .. versionchanged:: 3.0
        Generate ``https://`` links for URLs without a scheme.
    .. versionchanged:: 3.0
        The parsing rules were updated. Recognize email addresses with
        or without the ``mailto:`` scheme. Validate IP addresses. Ignore
        parentheses and brackets in more cases.
    """
    urls = list()
    if trim_url_limit is not None:

        def trim_url(x: str) -> str:
            if len(x) > trim_url_limit:  # type: ignore
                return f"{x[:trim_url_limit]}..."

            return x

    else:

        def trim_url(x: str) -> str:
            return x

    words = re.split(r"(\s+)", str(markupsafe.escape(text)))
    rel_attr = f' rel="{markupsafe.escape(rel)}"' if rel else ""
    target_attr = f' target="{markupsafe.escape(target)}"' if target else ""

    for i, word in enumerate(words):
        head, middle, tail = "", word, ""
        match = re.match(r"^([(<]|&lt;)+", middle)

        if match:
            head = match.group()
            middle = middle[match.end() :]

        # Unlike lead, which is anchored to the start of the string,
        # need to check that the string ends with any of the characters
        # before trying to match all of them, to avoid backtracking.
        if middle.endswith((")", ">", ".", ",", "\n", "&gt;")):
            match = re.search(r"([)>.,\n]|&gt;)+$", middle)

            if match:
                tail = match.group()
                middle = middle[: match.start()]

        # Prefer balancing parentheses in URLs instead of ignoring a
        # trailing character.
        for start_char, end_char in ("(", ")"), ("<", ">"), ("&lt;", "&gt;"):
            start_count = middle.count(start_char)

            if start_count <= middle.count(end_char):
                # Balanced, or lighter on the left
                continue

            # Move as many as possible from the tail to balance
            for _ in range(min(start_count, tail.count(end_char))):
                end_index = tail.index(end_char) + len(end_char)
                # Move anything in the tail before the end char too
                middle += tail[:end_index]
                tail = tail[end_index:]

        if _http_re.match(middle):
            urls.append(middle)
            if middle.startswith("https://") or middle.startswith("http://"):
                middle = f'<a href="{middle}"{rel_attr}{target_attr}>[{urllib.parse.urlparse(middle).hostname}]</a>'
            else:
                middle = (
                    f'<a href="https://{middle}"{rel_attr}{target_attr}>'
                    f"[{urllib.parse.urlparse(middle).hostname}]</a>"
                )

        elif middle.startswith("mailto:") and _email_re.match(middle[7:]):
            urls.append(middle)
            middle = f'<a href="{middle}">{middle[7:]}</a>'

        elif (
            "@" in middle
            and not middle.startswith("www.")
            and ":" not in middle
            and _email_re.match(middle)
        ):
            urls.append(middle)
            middle = f'<a href="mailto:{middle}">{middle}</a>'

        elif extra_schemes is not None:
            for scheme in extra_schemes:
                if middle != scheme and middle.startswith(scheme):
                    middle = f'<a href="{middle}"{rel_attr}{target_attr}>[{urllib.parse.urlparse(middle).hostname}]</a>'

        words[i] = f"{head}{middle}{tail}"

    return "".join(words), urls
