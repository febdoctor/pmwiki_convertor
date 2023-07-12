#!/usr/bin/env python3
"""
Extract all versions from PmWiki page files.

This module parses all edits in PmWiki page files. From that, it computes
all versions of that page sorted by time.

Each version is a tuple of:

  * time in seconds since epoch (1970/1/1)
  * extracted version dict (all optional):
     * text: the PmWiki formatted text of that version
     * csum: change summary
     * author: who last modified the text in that version
     * filename: name of the page

Requirement:

  * Python3
  * WhatThePatch module

Copyright (C) 2023 François Beerten

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import sys
import whatthepatch as wtp
import os


def unescape(line):
    # Replaces linebreaks with nothing newlines
    converted = line.replace("%0a", "\n")
    # Reencode %25 to %
    converted = converted.replace("%25", "%")
    # Reencode %3c to <
    converted = converted.replace("%3c", "<")
    return converted


def extractversions(pagename, page):
    current = {'filename': pagename}
    versions = {}
    for line in page:
        line = line.strip()
        k,v = line.split('=', 1)
        if ':' not in k:
            if k == 'text':
                v = unescape(v)
            current[k] = v
        else:
            k,t = k.split(':')[:2]
            t = int(t)
            ver = versions.get(t, {'filename': pagename, 'time':t})
            if k == 'diff':
                v = unescape(v)
                v = v.replace('\\ No newline at end of file', '')
            ver[k] = v
            versions[t] = ver
    versions = list(versions.items())
    versions.sort(reverse=True)
    lasttext = current['text']
    try:
        for t,v in versions:
            if 'diff' not in v:
                continue
            difftext = v.get('diff').replace('{{','[[').replace('}}',']]')
            diff = list(wtp.parse_patch(difftext))
            for i in diff:
                lasttext = wtp.apply_diff(i, lasttext)
            v['text'] = lasttext
    except wtp.exceptions.HunkApplyException as e:
        print(e)
    current['time'] = int(current['time'])
    current['text'] = current['text'].split('\n')
    versions.sort()
    versions.append((current['time'], current))
    return versions


def extractall(directory, files):
    versions = []
    for fname in files:
        if ',del-' in fname:
            print(f'Skipping ${fname}')
            continue
        print(fname)
        with open(os.path.join(directory, fname), 'rt', encoding="ISO-8859-1") as page:
            pageversions = extractversions(fname, page)
            versions += pageversions
    numbers = [i[0] for i in versions]
    versions.sort(key=lambda x: x[0])
    # remove simultaneous edits as those are likely spam
    times = [i[0] for i in versions]
    dups = [i for i in times if times.count(i) > 1]
    versions = [i for i in versions if i not in dups]
    return versions


def main():
    pagename = sys.argv[1]
    with open(pagename, "rt") as page:
        versions = parsepmwikipage(pagename, page)
    for t,v in versions:
        if not v.get('text'):
            continue
        print(t, v.get('author'), '*' * 20)
        print('\n'.join(v.get('text')))
        print()

if __name__ == '__main__':
    main()
