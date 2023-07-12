#!/usr/bin/env python3
"""
Convert versions into markdown pages in a git repo

Requirement:

  * Python3
  * WhatThePatch module
  * GitPython

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
import convertors
from git import Repo, Actor
import extractpmwiki
import datetime


class GitConvertor:
    def __init__(self, outdir, defaultcategory='Main', email_domain='example.com'):
        self.textconvertor = convertors.MarkdownConvertor()
        self.outdir = outdir
        self.repo = Repo(outdir)
        self.defaultcategory = defaultcategory
        self.emaildomain = email_domain


    def convert_files(self, directory, filenames, spamkeywords=[]):
        versions = extractpmwiki.extractall(directory, filenames)
        for t,v in versions:
            if not v.get('text'):
                continue
            text = v.get('text')
            if any((k in ' '.join(text)) for k in spamkeywords):
                    continue
            outfilename = self.textconvertor.get_output_filename(v['filename'])
            wiki_namespace, wiki_file = outfilename.split(".", 1)
            if wiki_namespace == self.defaultcategory:
                wiki_namespace = ''
            outpath = os.path.join(self.outdir, wiki_namespace, wiki_file)
            dirpath = os.path.dirname(outpath)
            os.makedirs(dirpath, exist_ok=True)
            pmwikinamespace = os.path.dirname(v['filename'])
            line = 'text=' + '\n'.join(v['text'])
            text = self.textconvertor.convert_line(line, pmwikinamespace)
            with open(outpath, 'wt') as f:
                f.write(text)
            gitpath = os.path.join(wiki_namespace, wiki_file)
            self.git_commit(v, gitpath)

    def git_commit(self, v, outpath):
        index = self.repo.index
        index.add([outpath])
        author = v.get('author', 'Unknown author')
        actor = Actor(author, author.replace(' ', '_') + '@' + self.emaildomain)
        commitmsg = '%s: %s' % (v['filename'], v.get('csum', f'Edit by {author}'))
        cdate = datetime.datetime.utcfromtimestamp(v['time']).isoformat()
        index.commit(commitmsg, author=actor, committer=actor,
            author_date=cdate, commit_date=cdate)
