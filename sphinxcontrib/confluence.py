# -*- coding: utf-8 -*-
"""
    sphinx.builders.text
    ~~~~~~~~~~~~~~~~~~~~

    Plain-text Sphinx builder.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path
import getpass

from .confluence_connect import Confluence
from .rst2conf import Writer
from docutils.io import StringOutput
from sphinx.builders import Builder
from sphinx.writers.text import TextWriter


class ConfluenceWriter(Writer):
    supported = ('confluence', )


class ConfluenceBuilder(Builder):
    name = 'confluence'
    format = 'html'
    out_suffix = '.txt'

    def init(self):
        username = input("Username: ")
        password = getpass.getpass()
        self.confluence = Confluence(url="https://confluence.smaato.net", username=username, password=password)

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.env.doc2path(docname, self.outdir,
                                           self.out_suffix)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None):
        return ''

    def prepare_writing(self, docnames):
        self.writer = TextWriter(self)
        self.confluence_writer = ConfluenceWriter()

    def write_doc(self, docname, doctree):
        """
        Write document to confluence
        :param docname:
        :param doctree:
        :return:
        """
        self.current_docname = docname
        destination = StringOutput(encoding='utf-8')

        self.confluence_writer.write(doctree, destination)

        confluence_info = doctree.children[0].children[0]
        for child in doctree.children:
            if child[0].startswith('confluence'):
                _, space, name = child[0].split(':')
                self.confluence.storePageContent(name, space, self.confluence_writer.output)
                break

    def finish(self):
        pass


def setup(app):
    app.add_builder(ConfluenceBuilder)