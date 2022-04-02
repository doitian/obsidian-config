#!/usr/bin/env python3

import subprocess
import tempfile
import os
import csv
import re
import urllib.parse
import filecmp
from pathlib import Path
from datetime import datetime

INVALID_CHARS_RE = re.compile(r'[\[\]\'?*#：|｜,\\/:" ]+')


def safe_name(name):
    return INVALID_CHARS_RE.sub(' ', name).strip()


def brief_authors(authors):
    if '&' in authors:
        return safe_name(authors.split('&')[0].strip()) + ' et al'
    return safe_name(authors)


export_dir = Path.home() / 'Dropbox' / 'Brain' / '3 Resources' / 'Calibre'
csv_fd, csv_path = tempfile.mkstemp(suffix='.csv', text=True)
csv_path = Path(csv_path)

try:
    subprocess.check_call(['calibredb', 'catalog', str(csv_path)])
    csv_io = os.fdopen(csv_fd, encoding='utf-8-sig')
    csv_reader = csv.DictReader(csv_io)
    for row in csv_reader:
        tmp_md_fd, tmp_md_path = tempfile.mkstemp(suffix='.md', text=True)
        md_file = export_dir / 'Calibre {} - {} - {}.md'.format(
            row['id'], brief_authors(row['authors']), safe_name(row['title'])
        )

        with os.fdopen(tmp_md_fd, 'w') as md_io:
            print('# {}'.format(row['title']), file=md_io)
            print('', file=md_io)
            tags = ['#{}'.format(tag) for tag in row['tags'].split(', ')]
            tags.append('#from/calibre')

            if 'eng' in row['languages']:
                tags.append('#lang/en')
            if 'zho' in row['languages']:
                tags.append('#lang/zh')

            tags = tags + ['#format/{}'.format(f)
                           for f in row['formats'].split(', ')]

            if row['rating'] != '':
                tags.append('#rating/{}'.format(row['rating']))
            else:
                tags.append('[[Books to Read]]')

            print(' '.join(tags), file=md_io)

            print('', file=md_io)
            print('## Meta', file=md_io)
            print('', file=md_io)
            print('- Authors:', end='', file=md_io)
            for author in row['authors'].split('&'):
                author = safe_name(author.strip())
                print(' [[{}]]'.format(author), end='', file=md_io)
            print('', file=md_io)
            if row['publisher'] != '':
                print('- Publisher: {}'.format(row['publisher']), file=md_io)
            pubdate = datetime.fromisoformat(row['pubdate'])
            if pubdate.year > 1000:
                print(
                    '- Publish Date: [[{}]]'.format(pubdate.strftime('%Y-%m-%d')), file=md_io)
            updated = datetime.fromisoformat(row['timestamp'])
            if updated.year > 1000:
                print(
                    '- Last Updated On: [[{}]]'.format(updated.strftime('%Y-%m-%d')), file=md_io)
            if row['series'] != '':
                print(
                    '- In Series: [[{}]]'.format(safe_name(row['series'])), file=md_io)

            print(
                '- [Open in Calibre](calibre://show-book/Calibre_Library/{})'.format(row['id']), file=md_io)

            if row['cover'] != '':
                dir = Path(row['cover']).parent
                dropbox_path = Path(*dir.parts[dir.parts.index('Dropbox') + 1:])
                print('- [Open Directory in Dropbox](https://www.dropbox.com/home/{})'.format(
                    urllib.parse.quote(str(dropbox_path))), file=md_io)
                print('- [Open Directory Locally](file://{}) (macOS Only)'.format(
                    urllib.parse.quote(str(dir))), file=md_io)

            if row['comments'] != '':
                print('', file=md_io)
                print('## Comments', file=md_io)
                print(row['comments'], file=md_io)

        tmp_md_path = Path(tmp_md_path)
        if not md_file.exists() or not filecmp.cmp(tmp_md_path, md_file, shallow=False):
            print('New: {}'.format(md_file.name))
            os.replace(tmp_md_path, md_file)
        else:
            # print('Same: {}'.format(md_file.name))
            pass

        # example_row = {
        #     'author_sort': 'Young, Scott',
        #     'authors': 'Scott Young',
        #     'comments': '',
        #     'cover': '/Users/ian/Dropbox/Calibre Library/Scott Young/Ultralearning - Shortform Summary (362)/cover.jpg',
        #     'formats': 'pdf',
        #     'id': '362',
        #     'identifiers': '',
        #     'isbn': '',
        #     'languages': '',
        #     'library_name': 'Calibre Library',
        #     'pubdate': '0101-01-01T08:00:00+08:00',
        #     'publisher': 'Shortform',
        #     'rating': '',
        #     'series': '',
        #     'series_index': '1.0',
        #     'size': '760825',
        #     'tags': 'shortform',
        #     'timestamp': '2021-08-01T12:06:12+08:00',
        #     'title': 'Ultralearning - Shortform Summary',
        #     'title_sort': 'Ultralearning - Shortform Summary',
        #     'uuid': 'f892b83f-8591-4575-8679-e68720c70ff7'
        # }

finally:
    csv_path.unlink()
