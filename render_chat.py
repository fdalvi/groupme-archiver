import argparse
import html
import json
import os
import sys
import time

from yattag import Doc

# Constants
__SYSTEM__ = "GroupMe"
FONT_URL = "https://fonts.googleapis.com/css?family=Open+Sans"


def css_file():
    return """
    .message_container {
        font-family: 'Open Sans', sans-serif;
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
        background-color: red;
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
    }

    /* Tooltip container */
    .tooltip {
        position: relative;
        display: inline-block;
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


def render_time_message(page_elements, message, prev_time):
    doc, tag, text = page_elements

    # Handle change in day
    message_time = time.localtime(message['created_at'])

    if prev_time is None or prev_time.tm_mday != message_time.tm_mday:
        with tag('div', klass='message_container'):
            doc.attr(style="background-color: #e4e4e4")
            with tag('span', klass='system_message'):
                text(time.strftime('%b %d, %Y at %-I:%M %p', message_time))

    return message_time


def render_system_message(page_elements, message):
    doc, tag, text = page_elements

    message_time = time.localtime(message['created_at'])
    with tag('div', klass='message_container'):
        doc.attr(title=time.strftime('%b %d, %Y at %-I:%M %p', message_time))
        doc.attr(style="background-color: #e4e4e4")
        with tag('span', klass='system_message'):
            text(message['text'] or '<ATTACHMENT>')


def render_message(page_elements, people, message):
    doc, tag, text = page_elements

    # Process mentions
    mentions = []
    for a in message['attachments']:
        if a['type'] == "mentions":
            mentions += a['loci']

    message_time = time.localtime(message['created_at'])
    with tag('div', klass='message_container'):
        doc.attr(title=time.strftime('%b %d, %Y at %-I:%M %p', message_time))
        with tag('div', klass='avatar'):
            pass
        with tag('div', klass='message_box'):
            with tag('span', klass='user'):
                text(people[message['author']]['name'])
            with tag('span', klass='message'):
                full_text = message['text'] or '<ATTACHMENT>'
                text_parts = []
                prev_end = 0

                for m in mentions:
                    start = m[0]
                    end = start + m[1]

                    text_parts.append((full_text[prev_end:start], 'normal'))
                    text_parts.append((full_text[start:end], 'bold'))
                    prev_end = end

                text_parts.append((full_text[prev_end:], 'normal'))

                for t, style in text_parts:
                    with tag('span'):
                        doc.attr('style="font-weight: %s;"' % (style))
                        text(t)
        with tag('span', klass='likes'):
            if len(message['favorited_by']) > 0:
                doc.attr(klass='likes tooltip')
                doc.asis("<img src='../assets/heart-full.png'></img>")
                doc.text(len(message['favorited_by']))
            else:
                doc.asis("<img src='../assets/heart.png'></img>")
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
                                                    prev_time)

                    # Check message type
                    if people[message['author']]['name'] == __SYSTEM__:
                        # Render system message
                        render_system_message(page_elements, message)
                    else:
                        # Render normal message
                        render_message(page_elements, people, message)

    # Save rendered files
    with open(os.path.join(args.input_dir, 'rendered.html'), 'w') as fp:
        fp.write(doc.getvalue())

    with open(os.path.join(args.input_dir, 'main.css'), 'w') as fp:
        fp.write(css_file())


if __name__ == '__main__':
    main()
