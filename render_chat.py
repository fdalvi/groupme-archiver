import argparse
import html
import json
import os
import sys
import time

from yattag import Doc


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

    .message_box {
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        margin-left: 10px;
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
    """


# Constants
__SYSTEM__ = "GroupMe"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', '-i', dest='input_dir', required=True)

    args = parser.parse_args()

    if not os.path.exists(os.path.join(args.input_dir, 'people.json')) or \
       not os.path.exists(os.path.join(args.input_dir, 'messages.json')):
        print("Missing files!")
        sys.exit(1)

    with open(os.path.join(args.input_dir, 'people.json')) as fp:
        people = json.load(fp)

    with open(os.path.join(args.input_dir, 'messages.json')) as fp:
        messages = json.load(fp)

    doc, tag, text = Doc().tagtext()

    prev_message_timestamp = 0
    with tag('html'):
        with tag('head'):
            doc.asis('<meta charset="utf-8">')
            doc.asis('<link href="https://fonts.googleapis.com/css?family=Open+Sans" rel="stylesheet">')
            doc.asis('<link rel="stylesheet" href="main.css">')
        with tag('body'):
            with tag('div', id='container'):
                with tag('h1'):
                    text('Stuff')
                for message in messages:
                    # Handle change in day
                    message_time = time.localtime(message['created_at'])
                    prev_message_time = time.localtime(prev_message_timestamp)

                    if prev_message_timestamp == 0 or prev_message_time.tm_mday != message_time.tm_mday:
                        with tag('div', klass='message_container'):
                            doc.attr(style="background-color: #e4e4e4")
                            with tag('span', klass='system_message'):
                                text(time.strftime('%b %d, %Y at %-I:%M %p', message_time))
                    prev_message_timestamp = message['created_at']

                    # Render message
                    with tag('div', klass='message_container'):
                        doc.attr(title=time.strftime('%b %d, %Y at %-I:%M %p', message_time))
                        if people[message['author']]['name'] == __SYSTEM__:
                            doc.attr(style="background-color: #e4e4e4")
                            with tag('span', klass='system_message'):
                                text(message['text'] or 'None')
                        else:
                            with tag('div', klass='avatar'):
                                pass
                            with tag('div', klass='message_box'):
                                with tag('span', klass='user'):
                                    text(people[message['author']]['name'])
                                with tag('span', klass='message'):
                                    text(message['text'] or 'None')

    with open(os.path.join(args.input_dir, 'rendered.html'), 'w') as fp:
        fp.write(doc.getvalue())

    with open(os.path.join(args.input_dir, 'main.css'), 'w') as fp:
        fp.write(css_file())


if __name__ == '__main__':
    main()
