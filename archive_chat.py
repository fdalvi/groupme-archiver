import argparse
import json
import os
import requests
import sys

from tabulate import tabulate


def list_groups(args):
    headers = {'Content-Type': 'application/json'}
    page_num = 1
    listing_complete = False

    chats = []
    while not listing_complete:
        params = {
            'token': args.token,
            'omit':  'memberships',
            'page':  page_num
        }
        r = requests.get('https://api.groupme.com/v3/groups',
                         headers=headers, params=params)

        current_chats = json.loads(r.content)

        for chat in current_chats['response']:
            chats.append((chat['name'], chat['id'], chat['messages']['count']))

        page_num += 1
        if len(current_chats['response']) == 0:
            listing_complete = True

    return chats


def main():
    parser = argparse.ArgumentParser(description="""GroupMe chats archiver.
        By default, the app will list all of your chats that are currently
        active.
        """)

    parser.add_argument('--token', '-t', required=True,
                        help="GroupMe Developer Token")
    parser.add_argument('--chat', '-c', help="Chat ID to archive")
    parser.add_argument('--output-dir', '-o', dest="output_dir",
                        help="Output directory to store archived content")

    args = parser.parse_args()

    if not args.chat:
        chats = list_groups(args)
        table_headers = ["Chat Name", "ID", "Number of messages"]
        print(tabulate(chats, headers=table_headers))
    else:
        if not args.output_dir:
            print("Please specify an output directory.")
            sys.exit(1)

        os.makedirs(args.output_dir, exist_ok=True)

        params = {
            'token': args.token
        }
        url = 'https://api.groupme.com/v3/groups/%s/messages' % (args.chat)
        r = requests.get(url, params=params)

        people = {}
        messages = []

        curr_messages = json.loads(r.content)

        # TODO Check for validity of request
        num_total_messages = curr_messages['response']['count']
        num_fetched_messages = 0
        curr_messages = curr_messages['response']['messages']

        print("Fetching %d messages..." % (num_total_messages))
        while True:
            num_fetched_messages += len(curr_messages)
            for message in curr_messages:
                if message['sender_id'] not in people:
                    people[message['sender_id']] = {
                        'name': message['name'],
                        'avatar_url': message['avatar_url']
                    }
                print("[%s] %s : %s" % (
                    message['created_at'], message['name'], message['text']))
                messages.append({
                    'author': message['sender_id'],
                    'created_at': message['created_at'],
                    'text': message['text'],
                    'favorited_by': message['favorited_by'],
                    'attachments': message['attachments']
                })
            last_message_id = curr_messages[-1]['id']

            params = {
                'token': args.token,
                'before_id': last_message_id,
                'limit': 20
            }
            url = 'https://api.groupme.com/v3/groups/%s/messages' % (args.chat)
            r = requests.get(url, params=params)

            if r.status_code == 304:
                break
            curr_messages = json.loads(r.content)

            # TODO Check for validity of request
            curr_messages = curr_messages['response']['messages']

        messages = list(reversed(messages))

        print("People:")
        table_headers = {
            "id": "ID",
            "name": "Name",
            "avatar_url": "Avatar URL"
        }
        print(tabulate([dict({'id': k}, **v) for (k, v) in people.items()],
                       headers=table_headers))

        # Save people
        with open(os.path.join(args.output_dir, "people.json"), 'w', encoding= 'utf-8') as fp:
            json.dump(people, fp, ensure_ascii=False)

        # Save messages
        with open(os.path.join(args.output_dir, "messages.json"), 'w', encoding= 'utf-8') as fp:
            json.dump(messages, fp, ensure_ascii=False)



if __name__ == '__main__':
    main()
