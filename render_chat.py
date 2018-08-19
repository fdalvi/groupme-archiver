import argparse
from datetime import datetime
import glob
import html
import json
import os
import pytz
import shutil
import sys
import time

from yattag import Doc

# Constants
__SYSTEM__ = "GroupMe"
FONT_URL = "https://fonts.googleapis.com/css?family=Open+Sans"


def css_file():
    return """
    .message_container {
        display: flex;
        flex-direction: row;
        padding-top: 5px;
        padding-bottom: 5px;
        justify-content: center;
    }

    .avatar {
        width: 40px;
        height: 40px;
        flex-basis: 40px;
        flex-shrink: 0;
        background-color: #3A61BF;

        display: flex;
        justify-content: center;
        align-items: center;

        color: #FFFFFF;

        border-radius: 50%;
    }

    .avatar > img {
        width: 40px;
        height: 40px;

        border-radius: 50%;
    }

    .likes {
        width: 30px;
        height: 30px;
        flex-basis: 30px;
        flex-shrink: 0;

        display: flex;
        justify-content: flex-start;
        align-items: flex-end;

        font-size: 10px;
        color: #bbb;
    }

    .likes > img {
        max-width: 70%;
        max-height: 70%;

        align-self: center;
    }

    .message_box {
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        margin-left: 10px;
        margin-right: 10px;
    }

    .message {
        white-space: pre-line;
        overflow-wrap: break-word;
        word-break: break-word;
    }

    .message > img {
        max-width: 400px;
        max-height: 400px;
    }

    .message > video {
        max-width: 400px;
        max-height: 400px;
    }

    .system_message {
        width: 80%;

        text-align: center;
        font-size: 14px;
        font-weight: bold;
        color: #666666;
    }

    .user {
        color: #555555;
        font-size: 14px;
    }

    #container {
        width: 768px;
    }

    body {
        background-color: #eeeeee;
        display: flex;
        flex-direction: row;
        justify-content: center;

        font-family: 'Open Sans', sans-serif;
    }

    /* Tooltip container */
    .tooltip {
        position: relative;
    }

    /* Tooltip text */
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: black;
        color: #fff;
        text-align: center;
        padding: 5px 0;
        border-radius: 6px;

        /* Position the tooltip text - see examples below! */
        position: absolute;
        z-index: 1;

        width: 120px;
        top: 100%;
        left: 30%;
        margin-left: -60px;
    }

    /* Show the tooltip text when you mouse over the tooltip container */
    .tooltip:hover .tooltiptext {
        visibility: visible;
    }

    .tooltip .tooltiptext::after {
        content: " ";
        position: absolute;
        bottom: 100%;  /* At the top of the tooltip */
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: transparent transparent black transparent;
    }
    """


def render_time_message(page_elements, message, prev_time, timezone=None):
    doc, tag, text = page_elements

    # Handle change in day
    message_time = datetime.fromtimestamp(message['created_at'], timezone)

    if prev_time is None or prev_time.day != message_time.day:
        with tag('div', klass='message_container'):
            doc.attr(style="background-color: #e4e4e4")
            with tag('span', klass='system_message'):
                text(message_time.strftime('%b %d, %Y at %-I:%M %p'))

    return message_time


def render_system_message(page_elements, message, timezone=None):
    doc, tag, text = page_elements

    message_time = datetime.fromtimestamp(message['created_at'], timezone)
    with tag('div', klass='message_container'):
        doc.attr(title=message_time.strftime('%b %d, %Y at %-I:%M %p'))
        doc.attr(style="background-color: #e4e4e4")
        with tag('span', klass='system_message'):
            text(message['text'] or '<ATTACHMENT>')


def render_avatar(input_dir, page_elements, people, message):
    doc, tag, text = page_elements

    avatar_url = people[message['author']]['avatar_url']
    if avatar_url:
        avatar_path = "%s.avatar" % (message['author'])
        avatar_path = os.path.join('avatars', avatar_path)
        avatar_path = glob.glob("%s/%s*" % (input_dir, avatar_path))[0]
        avatar_path = "/".join(avatar_path.split('/')[-2:])
        doc.asis('<img src="%s"></img>' % (avatar_path))
    else:
        names = people[message['author']]['name'].split()
        shorthand = names[0][0].upper()
        if len(names) > 1:
            shorthand += names[-1][0].upper()
        text(shorthand)


def render_message(input_dir, page_elements, people, message, timezone=None):
    doc, tag, text = page_elements

    # Process mentions
    mentions = []
    for a in message['attachments']:
        if a['type'] == "mentions":
            mentions += a['loci']

    message_time = datetime.fromtimestamp(message['created_at'], timezone)
    with tag('div', klass='message_container'):
        doc.attr(title=message_time.strftime('%b %d, %Y at %-I:%M %p'))
        with tag('div', klass='avatar'):
            render_avatar(input_dir, page_elements, people, message)
        with tag('div', klass='message_box'):
            with tag('span', klass='user'):
                text(people[message['author']]['name'])
            if len(message['attachments']) > 0:
                for att in message['attachments']:
                    if att['type'] == 'image' or \
                       att['type'] == 'linked_image':
                        image_path = att['url'].split('/')[-1]
                        image_path = os.path.join('attachments', image_path)
                        r = glob.glob("%s/%s*" % (input_dir, image_path))
                        image_path = r[0]
                        image_path = "/".join(image_path.split('/')[-2:])
                        with tag('span', klass='message'):
                            doc.asis('<img src="%s"></img>' % (
                                image_path))
                    elif att['type'] == 'video':
                        video_path = att['url'].split('/')[-1]
                        video_path = os.path.join('attachments', video_path)
                        r = glob.glob("%s/%s*" % (input_dir, video_path))[0]
                        video_path = r
                        video_path = "/".join(video_path.split('/')[-2:])
                        with tag('span', klass='message'):
                            doc.asis('<video src="%s" controls></video>' % (
                                video_path))
            if message['text']:
                with tag('span', klass='message'):
                    _text = message['text']

                    # Remove video urls
                    for att in message['attachments']:
                        if att['type'] == 'video':
                            start_idx = _text.find(att['url'])
                            end_idx = start_idx + len(att['url'])
                            _text = _text[:start_idx] + _text[end_idx:]

                    # Split text into mentions and normal text
                    text_parts = []
                    prev_end = 0

                    for m in mentions:
                        start = m[0]
                        end = start + m[1]

                        text_parts.append((_text[prev_end:start], 'normal'))
                        text_parts.append((_text[start:end], 'bold'))
                        prev_end = end

                    text_parts.append((_text[prev_end:], 'normal'))

                    for t, style in text_parts:
                        with tag('span'):
                            doc.attr('style="font-weight: %s;"' % (style))
                            text(t)
        with tag('span', klass='likes'):
            if len(message['favorited_by']) > 0:
                doc.attr(klass='likes tooltip')
                doc.asis("<img src='assets/heart-full.png'></img>")
                doc.text(len(message['favorited_by']))
            else:
                doc.asis("<img src='assets/heart.png'></img>")
            with tag('div', klass='tooltiptext'):
                for id in message['favorited_by']:
                    name = "Unknown"
                    if id in people:
                        name = people[id]['name']
                    with tag('div'):
                        text(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', '-i', dest='input_dir', required=True)
    parser.add_argument('--timezone', type=str,
                        help="Timezone to render message times in.")

    args = parser.parse_args()

    if not os.path.exists(os.path.join(args.input_dir, 'people.json')) or \
       not os.path.exists(os.path.join(args.input_dir, 'messages.json')) or \
       not os.path.exists(os.path.join(args.input_dir, 'group_info.json')):
        print("Missing files!")
        sys.exit(1)

    with open(os.path.join(args.input_dir, 'people.json')) as fp:
        people = json.load(fp)

    with open(os.path.join(args.input_dir, 'messages.json')) as fp:
        messages = json.load(fp)

    with open(os.path.join(args.input_dir, 'group_info.json')) as fp:
        group_info = json.load(fp)

    page_elements = Doc().tagtext()
    doc, tag, text = page_elements

    tz = None
    if args.timezone:
        tz = pytz.timezone(args.timezone)

    prev_time = None
    with tag('html'):
        with tag('head'):
            doc.asis('<meta charset="utf-8">')
            doc.asis('<link href="%s" rel="stylesheet">' % (FONT_URL))
            doc.asis('<link rel="stylesheet" href="main.css">')
        with tag('body'):
            with tag('div', id='container'):
                with tag('h1'):
                    text(group_info['name'])

                # Render messages
                for message in messages:
                    # Check and render time divider
                    prev_time = render_time_message(page_elements, message,
                                                    prev_time, tz)

                    # Check message type
                    if people[message['author']]['name'] == __SYSTEM__:
                        # Render system message
                        render_system_message(page_elements, message,
                                              tz)
                    else:
                        # Render normal message
                        render_message(args.input_dir, page_elements, people,
                                       message, tz)

    # Save rendered files
    with open(os.path.join(args.input_dir, 'rendered.html'), 'w') as fp:
        fp.write(doc.getvalue())

    with open(os.path.join(args.input_dir, 'main.css'), 'w') as fp:
        fp.write(css_file())

    root_path = os.path.realpath(__file__)
    assets_dir = os.path.join(os.path.dirname(root_path), 'assets')
    project_assets_dir = os.path.join(args.input_dir, 'assets')
    os.makedirs(project_assets_dir, exist_ok=True)
    shutil.copy(os.path.join(assets_dir, 'heart.png'), project_assets_dir)
    shutil.copy(os.path.join(assets_dir, 'heart-full.png'), project_assets_dir)


if __name__ == '__main__':
    main()
