import argparse
import glob
import json
import os
import requests
import sys
from tqdm import tqdm

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


def list_dms(args):
    headers = {'Content-Type': 'application/json'}
    page_num = 1
    listing_complete = False

    chats = []
    while not listing_complete:
        params = {
            'token': args.token,
            'page':  page_num
        }
        r = requests.get('https://api.groupme.com/v3/chats',
                         headers=headers, params=params)

        current_chats = json.loads(r.content)

        for chat in current_chats['response']:
            chats.append((
                        chat['other_user']['name'],
                        chat['other_user']['id'],
                        chat['messages_count']
                        ))

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
    parser.add_argument('--group-chat-id', '-g', dest="group_chat_id",
                        help="Group chat ID to archive")
    parser.add_argument('--num-messages-per-request', '-n', default=20,
                        dest='num_messages_per_request',
                        help="Number of messages in each request. Max: 100.")
    parser.add_argument('--output-dir', '-o', dest="output_dir",
                        help="Output directory to store archived content")

    parser.add_argument('--save-global-avatars', action='store_true',
                        dest='save_global_avatars',
                        help="Use global avatars instead of " +
                             "chat specific user avatars")

    args = parser.parse_args()

    if not args.group_chat_id:
        print("Group chats")
        print("===========")
        chats = list_groups(args)
        table_headers = ["Chat Name", "ID", "Number of messages"]
        print(tabulate(chats, headers=table_headers))

        print("")
        print("Direct Messages")
        print("===============")
        chats = list_dms(args)
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
        url = 'https://api.groupme.com/v3/groups/%s' % (args.group_chat_id)
        r = requests.get(url, params=params)

        people = {}
        messages = []
        group_info = {}

        response = json.loads(r.content)['response']

        group_info['name'] = response['name']
        group_info['description'] = response['description']
        group_info['image_url'] = response['image_url']
        group_info['created_at'] = response['created_at']

        for member in response['members']:
            people[member['user_id']] = {'name': member['nickname']}
            if args.save_global_avatars:
                people[member['user_id']]['avatar_url'] = member['image_url']
            else:
                people[member['user_id']]['avatar_url'] = None

        url = 'https://api.groupme.com/v3/groups/%s/messages' % (
               args.group_chat_id)
        r = requests.get(url, params=params)

        curr_messages = json.loads(r.content)

        # TODO Check for validity of request
        num_total_messages = curr_messages['response']['count']
        num_fetched_messages = 0
        curr_messages = curr_messages['response']['messages']
        all_attachments = []

        print("Fetching %d messages..." % (num_total_messages))
        pbar = tqdm(total=num_total_messages)
        while num_fetched_messages < num_total_messages:
            num_fetched_messages += len(curr_messages)
            pbar.update(len(curr_messages))
            for message in curr_messages:
                if message['sender_id'] not in people:
                    people[message['sender_id']] = {
                        'name': message['name'],
                        'avatar_url': message['avatar_url']
                    }
                if not args.save_global_avatars and \
                   people[message['sender_id']]['avatar_url'] is None:
                    people[message['sender_id']]['avatar_url'] = \
                        message['avatar_url']

                for att in message['attachments']:
                    if att['type'] == 'image' or \
                       att['type'] == 'video' or \
                       att['type'] == 'linked_image':
                        all_attachments.append(att['url'])
                # print("[%s] %s : %s" % (
                #    message['created_at'], message['name'], message['text']))
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
                'limit': args.num_messages_per_request
            }
            url = 'https://api.groupme.com/v3/groups/%s/messages' % (
                   args.group_chat_id)
            r = requests.get(url, params=params)

            if r.status_code == 304:
                break
            curr_messages = json.loads(r.content)

            # TODO Check for validity of request
            curr_messages = curr_messages['response']['messages']

        pbar.close()
        messages = list(reversed(messages))

        print("\nFetching avatars...")
        avatars_path = os.path.join(args.output_dir, 'avatars/')
        os.makedirs(avatars_path, exist_ok=True)
        for k, v in tqdm(people.items()):
            url = v['avatar_url']
            if url:
                r = requests.get("%s.avatar" % (url))
                img_type = r.headers['content-type'].split('/')[1]
                avatar_path = os.path.join(avatars_path,
                                           '%s.avatar.%s' % (k, img_type))
                with open(avatar_path, 'wb') as fp:
                    fp.write(r.content)

        print("\nFetching attachments...")
        attachments_path = os.path.join(args.output_dir, 'attachments/')
        os.makedirs(attachments_path, exist_ok=True)
        for att_url in tqdm(all_attachments):
            file_name = att_url.split('/')[-1]
            att_path = 'attachments/%s.%s' % (file_name, "*")
            att_full_path = os.path.join(args.output_dir, att_path)
            if len(glob.glob(att_full_path)) == 0:
                r = requests.get(att_url)
                img_type = r.headers['content-type'].split('/')[1]
                att_path = 'attachments/%s.%s' % (file_name, img_type)
                att_full_path = os.path.join(args.output_dir, att_path)

                with open(att_full_path, 'wb') as fp:
                    fp.write(r.content)

        print("\nPeople:")
        table_headers = {
            "id": "ID",
            "name": "Name",
            "avatar_url": "Avatar URL"
        }
        print(tabulate([dict({'id': k}, **v) for (k, v) in people.items()],
                       headers=table_headers))

        # Save everything
        people_file = os.path.join(args.output_dir, "people.json")
        messages_file = os.path.join(args.output_dir, "messages.json")
        group_info_file = os.path.join(args.output_dir, "group_info.json")

        # Save people
        with open(people_file, 'w', encoding='utf-8') as fp:
            json.dump(people, fp, ensure_ascii=False, indent=2)

        # Save messages
        with open(messages_file, 'w', encoding='utf-8') as fp:
            json.dump(messages, fp, ensure_ascii=False, indent=2)

        # Save group information
        with open(group_info_file, 'w', encoding='utf-8') as fp:
            json.dump(group_info, fp, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
