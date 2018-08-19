# GroupMe Archiver
<p align="center">
<img src="https://d3sq5bmi4w5uj1.cloudfront.net/images/brochure/logo.png?1513786503" height="50px"></img>
</p>

<p align="center">
<img src="https://openclipart.org/image/800px/svg_to_png/211761/matt-icons_go-down.png" height="40px" style="line-height:50px"></img>
</p>

<p align="center">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/JSON_vector_logo.svg/320px-JSON_vector_logo.svg.png" height="50px"></img> <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/HTML5_logo_and_wordmark.svg/240px-HTML5_logo_and_wordmark.svg.png" height="50px"></img>
</p>

Archive/Backup and Render GroupMe chats as JSON and HTML! GroupMe provides an [awesome dev API](https://dev.groupme.com) that lets you pull messages/attachments from their servers, and these scripts makes use of them. The `archive_chat.py` script allows you to list existing group/direct messages, and then fetch all information for any given group/direct message chat. All information is saved as `json` files, while the attachments and avatars are stored in their original format.

## Features
- Supports Group chats as well as Direct Message chats
- Rendering matches the mobile app interface to a high degree for a familiar experience
- Support for user avatars, _favorited by_ lists and mentions
- Support for image, linked images and video attachment types

## Installation
For setting up the dependencies, simple run:

```bash
conda env create -f conda-environment.yml
source activate groupme-archiver
```

If you do not have `conda` and want to go the manual route, you'll need to `pip install` the following dependencies: `pytz`, `requests`, `tabulate`, `tqdm` and `yattag`

You will also _need a token_ from GroupMe through which the scripts will access your data. You can get this token after you log in to https://dev.groupme.com (using your normal GroupMe credentials). The token is accessible by clicking **Access token** in the header. 

## Fetching your chats
Once you have everything setup and the access token in hand, just run

```bash
python archive_chat.py -t <access-token-here>
```

You existing groups and direct messages will be listed, along with their ID's. Find your chat of interest and note its ID down.

#### Group Chat
For group chats, run
```bash
python archive_chat.py -t <access-token-here> -g <group-id-here>
```

#### Direct Messages
For direct message chats, run
```bash
python archive_chat.py -t <access-token-here> -d <direct-chat-id-here>
```

Once you run one of the above commands, you will have a folder with the same name as the group (or the person in a direct chat). It will contain all of the information from the chat; the messages, avatars and attachments.

## Rendering your chats
You can either use the archived data in its raw JSON form, or you can render the entire chat as a nice HTML. 
```bash
python render_chat.py -i <folder-name-here>
```

A `rendered.html` file will be created in the same folder, which you can open in any browser to see a nicely formatted chat!

## More Options
The `archive_chat.py` has a few more options (use the `-h` flag to see them all):
- `--num-messages-per-request`, `-n`: Number of messages per request. The default is 20 as in the GroupMe API, but can be set to a value as big as 100 for faster message fetching. Consider setting this value if your chat has _a lot_ of messages.
- `--output-dir`, `-o`: Custom output folder - if you don't want the output to be saved in the predefined folder of the group/person name.
- `--save-global-avatars`: GroupMe allows you to set chat specific avatars/profile pics (and also change your avatar mid-chat). This option would use the global avatar for each user, instead of the latest avatar set within the chat of interest.

The `render_chat.py` has an extra option:
- `--timezone`: The timestamps can be adjusted by providing an entry from the [Olsen database](https://en.wikipedia.org/wiki/Tz_database), for e.g. `America/Los_Angeles`

## TODO/Wishlist
- [ ] Archiving: Resumable archiving (Partially done for attachments)
- [ ] Archiving: Multiple avatars per user within the same chat
- [ ] Archiving: Better error handling for mismatched ID's and failed API requests
- [ ] Render: Support for custom GroupMe emoji packs
- [x] Render: Support for multiple image/video attachments per message
