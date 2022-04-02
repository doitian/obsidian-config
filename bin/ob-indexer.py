#!/usr/bin/env python3

import subprocess
import tempfile
import os
import jinja2
import filecmp
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from itertools import chain, takewhile
from pathlib import Path

BEGIN_MARKER = '%%+BEGIN: indexer%%'
END_MARKER = '%%+END%%'


def build_item(path):
    item = dict({'stem': path.stem})

    with open(path) as rd:
        content = rd.read()

    lines = iter(content.splitlines())
    current_line = None

    try:
        current_line = next(lines)
        if current_line == '---':
            front_matters = yaml.load('\n'.join(takewhile(lambda x: x != '---', lines)), Loader=Loader)
            item.update(front_matters)
        elif current_line.startswith('# '):
            item['title'] = current_line[2:]
            current_line = next(lines)

        for line in chain([current_line], lines):
            if ':: ' in line:
                key, value = line.split(':: ', 1)
                item[key] = value
            else:
                break

    except StopIteration:
        pass

    if 'title' not in item:
        item['title'] = item['stem']
    if item['title'] == item['stem']:
        item['ref'] = f"[[{item['stem']}]]"
    else:
        item['ref'] = f"[[{item['stem']}|{item['title']}]]"
    return item


def render_index(find_line, template):
    template = jinja2.environment.Template(template)

    files = []
    for file in subprocess.check_output(find_line, shell=True).splitlines():
        path = Path(file.decode('utf-8'))
        files.append(build_item(path))

    return template.render(files=files)


def refresh_file(content, wt):
    find_line = None
    template = []
    state = 'normal'  # normal / indexer / jinja2 / output

    for line in content.splitlines():
        if state == 'normal':
            print(line, file=wt)
            if line == BEGIN_MARKER:
                state = 'indexer'
        elif state == 'indexer':
            print(line, file=wt)
            if line == '```jinja2':
                state = 'jinja2'
        elif state == 'jinja2':
            print(line, file=wt)
            if line == '```':
                print('', file=wt)
                print(render_index(find_line, '\n'.join(template)).strip(), file=wt)
                print('\n%%+END%%', file=wt)
                find_line = None
                template = []
                state = 'output'
            elif find_line is None:
                find_line = line[3:-3]
            else:
                template.append(line)
        elif state == 'output':
            if line == '%%+END%%':
                state = 'normal'


cwd = os.getcwd()

for file in subprocess.check_output(['rg', '-l', '%%\\+BEGIN: indexer%%']).splitlines():
    file = Path(file.decode('utf-8'))
    with open(file) as rd:
        content = rd.read()

    temp_fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, 'w') as wt:
            os.chdir(file.parent)
            refresh_file(content, wt)
            os.chdir(cwd)
        # print(open(temp_path).read(), end='')
        if not file.exists() or not filecmp.cmp(temp_path, file, shallow=False):
            os.replace(temp_path, file)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
