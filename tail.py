#
# function "tail" from https://stackoverflow.com/a/13790289
# copyright stackoverflow user glenbot


import os
import time

import humanize

import urlize


def is_chat_line(line):
    return line[11] == "<"


def ii_line_fmt(line):
    try:
        words = line.split()
        t = humanize.naturaldelta(time.time() - int(words[0]))
        if words[1][0] == "<":  # nickname
            new_line, _ = urlize.urlize(" ".join(words[2:]), target="blank")
            return int(words[0]), t, words[1], new_line
        else:
            return int(words[0]), t, "", " ".join(words[1:])
    except:
        return "", "", "", ""


def tail(f, lines=1, _buffer=1024):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    lines_found = [ii_line_fmt(line) for line in lines_found[-lines:]]
    return lines_found


def chat_only_tail(f, lines=1, _buffer=1024):
    lines_found = []
    block_counter = -1

    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:
            f.seek(0)
            data = f.readlines()
            for line in data:
                if is_chat_line(line):
                    lines_found.append(line)
            break

        data = f.readlines()
        for line in data:
            if is_chat_line(line):
                lines_found.append(line)
        block_counter -= 1

    lines_found = [ii_line_fmt(line) for line in lines_found[-lines:]]
    return lines_found
