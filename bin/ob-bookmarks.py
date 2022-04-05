#!/usr/bin/env python3

from pathlib import Path
import tempfile
import json
import textwrap
import hashlib
import os
import shutil
import filecmp

BOOKMARKLET_PREFIX = 'javascript:'
BOOKMARKLET_PREFIX_LEN = len(BOOKMARKLET_PREFIX)
DATA_URL_PREFIX = 'data:'
FOLDER_COMMENT_PREFIX = 'chrome://bookmarks/?id='

def export_bookmarks_folder(dir, folder):
    dir.mkdir(exist_ok=True)
    name = folder['name']

    with open(dir / f'{name} - Bookmarks.md', 'w') as md_file:
        print(f'# {name} - Bookmarks\n', file=md_file)
        print(f'#bookmarks #from/browser\n', file=md_file)

        for child in folder['children']:
            if child['type'] == 'folder':
                export_bookmarks_folder(dir / child['name'], child)
                print(f'- 📁 [[{child["name"]} - Bookmarks]]', file=md_file)
            else:
                url = child['url']
                sha = hashlib.sha256(url.encode('utf-8')).hexdigest()[:7]
                split_parts = child['name'].split(' \\\\ ')
                child_name = split_parts[0]
                description = '\n'.join(split_parts[1:])

                if url.startswith(BOOKMARKLET_PREFIX):
                    print(textwrap.dedent('''\
                        - {} #bookmarklet ^{}
                            ```javascript
                        {}
                            ```
                    ''').format(child_name, sha, textwrap.indent(url[BOOKMARKLET_PREFIX_LEN:], '    ')), file=md_file)
                elif url.startswith(DATA_URL_PREFIX):
                    print(textwrap.dedent('''\
                        - {} #bookmarklet ^{}
                            ```
                        {}
                            ```
                    ''').format(child_name, sha, textwrap.indent(url, '    ')), file=md_file)
                elif url.startswith(FOLDER_COMMENT_PREFIX):
                    print(child_name, file=md_file)
                    print('', file=md_file)
                else:
                    print(
                        f"- {child_name} [{url.split('://')[1].split('/')[0]}]({url}) ^{sha}", file=md_file)

                if description != '':
                    if not url.startswith(FOLDER_COMMENT_PREFIX):
                        print('', file=md_file)
                    print(textwrap.indent(description, '    '), file=md_file)
                    print('', file=md_file)


export_dir = Path.home() / 'Dropbox' / 'Brain' / '3 Resources' / 'Bookmarks'
tmp_dir = Path(tempfile.mkdtemp())

with (Path.home() / 'Library/Application Support/Google/Chrome/Profile 1/Bookmarks').open() as fd:
    root = json.load(fd)["roots"]
    merged_root = root["other"]
    merged_root["name"] = 'Roots'
    merged_root["children"] = [root["bookmark_bar"]] + merged_root["children"]
    export_bookmarks_folder(tmp_dir, merged_root)

for root, dirs, files in os.walk(tmp_dir):
    for f in files:
        src_file = Path(root) / f
        relative_path = src_file.relative_to(tmp_dir)
        target_file = export_dir / relative_path
        target_file.parent.mkdir(exist_ok=True)
        if not target_file.exists() or not filecmp.cmp(src_file, target_file, shallow=False):
            print('NEW:', relative_path)
            os.replace(src_file, target_file)
        else:
            # print('SKIP:', relative_path)
            pass

shutil.rmtree(tmp_dir)
