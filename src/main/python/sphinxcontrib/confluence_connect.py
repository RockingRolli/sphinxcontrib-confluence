#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import json
import copy
import os
import re
import sys
import ssl


import logging
import socket


def attach_file(server, token, space, title, files):
    existing_page = server.confluence1.getPage(token, space, title)

    for filename in files.keys():
        try:
            server.confluence1.removeAttachment(token, existing_page["id"] , filename)
        except:
            print("Skipping exception in removeAttachment")
        ty = "application/binary"
        if filename.endswith("gif"):
            ty = "image/gif"
        elif filename.endswith("png"):
            ty = "image/png"
        attachment = { "fileName": filename, "contentType": ty, "comment": files[filename] }
        f = open(filename, "rb")
        try:
            byts = f.read()
            print("calling addAttachment(%s, %s, %s, ...)" % (token, existing_page["id"], repr(attachment)))
            server.confluence1.addAttachment(token, existing_page["id"], attachment, xmlrpclib.Binary(byts))
            print("done")
        finally:
            f.close()


def remove_all_attachments(server, token, space, title):
    existing_page = server.confluence1.getPage(token, space, title)

    # Get a list of attachments
    files = server.confluence1.getAttachments(token, existing_page["id"])

    # Iterate through them all, removing each
    numfiles = len(files)
    i = 0
    for f in files:
        filename = f['fileName']
        print("Removing %d of %d (%s)..." % (i, numfiles, filename))
        server.confluence1.removeAttachment(token, existing_page["id"], filename)
        i += 1


def write_page(server, token, space, title, content, parent=None):
    parent_id = None
    if not parent is None:
        try:
            # Find out the ID of the parent page
            parent_id = server.confluence1.getPage(token, space, parent)['id']
            print("parent page id is %s" % parent_id)
        except:
            print("couldn't find parent page; ignoring error...")

    try:
        existing_page = server.confluence1.getPage(token, space, title)
    except:
        # In case it doesn't exist
        existing_page = {}
        existing_page["space"] = space
        existing_page["title"] = title

    if not parent_id is None:
        existing_page["parentId"] = parent_id

    existing_page["content"] = content
    existing_page = server.confluence1.storePage(token, existing_page)


class WikiString(str):
    pass


class XMLString(str):
    pass


class Confluence(object):

    DEFAULT_OPTIONS = {
        "server": "http://localhost:8090",
        "verify": True
    }

    def __init__(self, profile=None, url="http://localhost:8090/", username="admin", password="admin", appid=None):
        """
        Returns a Confluence object by loading the connection details from the `config.ini` file.

        :param profile: The name of the section from config.ini file that stores server config url/username/password
        :param url: URL of the Confluence server
        :param username: username to use for authentication
        :param password: password to use for authentication
        :return: Confluence -- an instance to a Confluence object.
        :raises: EnvironmentError

        Usage:

            >>> from confluence import Confluence
            >>>
            >>> conf = Confluence(profile='confluence')
            >>> conf.storePageContent("test","test","hello world!")

        Also create a `config.ini` like this and put it in current directory, user home directory or PYTHONPATH.

        .. code-block:: none

            [confluence]
            url=https://confluence.atlassian.com
            # only the `url` is mandatory
            user=...
            pass=...

        """
        def findfile(path):
            """
            Find the file named path in the sys.path.
            Returns the full path name if found, None if not found
            """
            paths = ['.', os.path.expanduser('~')]
            paths.extend(sys.path)
            for dirname in paths:
                possible = os.path.abspath(os.path.join(dirname, path))
                if os.path.isfile(possible):
                    return possible
            return None
        config = ConfigParser.SafeConfigParser(defaults={'user': None, 'pass': None, 'appid': appid})

        config_file = findfile('config.ini')

        if not profile:
            if config_file:
                config.read(config_file)
                try:
                    profile = config.get('general','default-confluence-profile')
                except ConfigParser.NoOptionError:
                    pass

        if profile:
            if config_file:
                config.read(config_file)
                url = config.get(profile, 'url')
                username = config.get(profile, 'user')
                password = config.get(profile, 'pass')
                appid = config.get(profile, 'appid')
            else:
                raise EnvironmentError("%s was not able to locate the config.ini file in current directory, user home directory or PYTHONPATH." % __name__)

        options = Confluence.DEFAULT_OPTIONS
        options['server'] = url
        options['username'] =  username
        options['password'] = password

        socket.setdefaulttimeout(120) # without this there is no timeout, and this may block the requests
        # 60 - getPages() timeout one with this !
        self._server = xmlrpclib.ServerProxy(options['server'] +  '/rpc/xmlrpc', allow_none=True) # using Server or ServerProxy ?
        #print self._server.system.listMethods()

        self._token = self._server.confluence1.login(username, password)
        try:
            self._token2 = self._server.confluence2.login(username, password)
        except:
            self._token2 = None

        #return (server, token)

        #return Confluence(options=options,basic_auth=(username,password))

    def getPage(self, page, space):
        """
        Returns a page object as a dictionary.

        :param page:
        :param space:
        :return: dictionary. result['content'] contains the body of the page.
        """
        if self._token2:
            page = self._server.confluence2.getPage(self._token2, space, page)
        else:
            page = self._server.confluence1.getPage(self._token, space, page)
        return page

    def getBlogEntries(self, space):
        """
        Returns a page object as a Vector.

        :param space:
        """
        if self._token2:
            entries = self._server.confluence2.getBlogEntries(self._token2, space)
        else:
            entries = self._server.confluence1.getBlogEntries(self._token, space)
        return entries

    def getBlogEntry(self, pageId):
        """
        Returns a blog page as a BlogEntry object.

        :param pageId:
        """
        if self._token2:
            entry  = self._server.confluence2.getBlogEntry(self._token2, pageId)
        else:
            entry  = self._server.confluence1.getBlogEntries(self._token, pageId)
        return entry

    def storeBlogEntry(self, entry):
        """
        Store or update blog content.
        (The BlogEntry given as an argument should have space, title and content fields at a minimum.)

        :param entry:
        :return: blogEntry: if succeeded
        """
        if self._token2:
            blogEntry = self._server.confluence2.storeBlogEntry(self._token2, entry)
        else:
            blogEntry = self._server.confluence1.storeBlogEntry(self._token2, entry)
        return blogEntry

    def addLabelByName(self, labelName, objectId):
        """
        Adds label(s) to the object.

        :param labelName (Tag Name)
        :param objectId (Such as pageId)
        :retuen: bool: True if succeeded
        """
        if self._token2:
            ret = self._server.confluence2.addLabelByName(self._token2, labelName, objectId)
        else:
            ret = self._server.confluence1.addLabelByName(self._token, labelName, objectId)
        return ret

    def getPageId(self, page, space):
        """
        Retuns the numeric id of a confluence page.

        :param page:
        :param space:
        :return: Integer: page numeric id
        """
        if self._token2:
            page = self._server.confluence2.getPage(self._token2, space, page)
        else:
            page = self._server.confluence1.getPage(self._token, space, page)
        return page['id']

    def storePageContent(self, page, space, content, convert_wiki=True):
        """
        Modifies the content of a Confluence page.

        :param page:
        :param space:
        :param content:
        :return: bool: True if succeeded
        """
        data = self.getPage(page, space)
        #print data
        data['content'] = content
        if self._token2:
            if convert_wiki:
                content = self._server.confluence2.convertWikiToStorageFormat(self._token2, content)
            data['content'] = content
            return self._server.confluence2.storePage(self._token2, data)
        else:
            return self._server.confluence1.storePage(self._token, data)

    def renderContent(self, space, page, a='', b=None):
        """
        Obtains the HTML content of a wiki page.

        :param space:
        :param page:
        :return: string: HTML content
        """
        try:
            if not page.isdigit(): #isinstance(page, numbers.Integral):
                page = self.getPageId(page=page, space=space)
            if self._token2:
                return self._server.confluence2.renderContent(self._token2, space, page, a, b)
            else:
                return self._server.confluence1.renderContent(self._token, space, page, a, b)
        #except Exception as e:
        except ssl.SSLError as err:
            logging.error("%s while retrieving page %s", err, page)
            return None
        except xmlrpclib.Fault as err:
            #logging.error("Fault code: %d" % err.faultCode)
            #logging.error("Fault string: %s" % err.faultString)
            #self.getPage(page, )
            logging.error("Failed call to renderContent('%s','%s') : %d : %s", space, page, err.faultCode, err.faultString)
            raise err
            #return ''

    def convertWikiToStorageFormat(self, markup):
        """
        Converts a wiki text to it's XML/HTML format. Useful if you prefer to generate pages using wiki syntax instead of XML.

        Still, remember that once you cannot retrieve the original wiki text, as confluence is not storing it anymore. \
        Due to this wiki syntax is usefull only for computer generated pages.

        Warning: this works only with Conflucence 4.0 or newer, on older versions it will raise an error.

        :param markup:
        :return:
        """
        if self._token2:
            return self._server.confluence2.convertWikiToStorageFormat(self._token2, markup)
        else:
            return self._server.confluence.convertWikiToStorageFormat(self._token2, markup)
            #raise NotImplementedError("You cannot convert Wiki to Storage ")

    def getSpaces(self):
        return self._server.confluence2.getSpaces(self._token2)

    def getPages(self, space):
        return self._server.confluence2.getPages(self._token2, space)

    def getPagesWithErrors(self, stdout=True, caching=True):
        result = []
        cnt = 0
        cnt_err = 0
        stats = {}
        data = {}
        pages = {}
        if caching:
            try:
                data = json.load(open('pages.json', 'r'))
                pages = copy.deepcopy(data)
                logging.info("%s pages loaded from cache.", len(pages.keys()))
            except IOError:
                pass
        if not data:
            spaces = self.getSpaces()
            for space in spaces:
                logging.debug("Space %s", space['key'])
                for page in self.getPages(space=space['key']):
                    pages[page['id']] = page['url']
            logging.info("%s pages loaded from confluence.", len(pages.keys()))


        for page in sorted(pages.keys()):
            cnt += 1
            # space['key']
            renderedPage = self.renderContent(None, page, '', {'style':'clean'})
            #dom = parseString(renderedPage)
            #for e in dom.getElementsByTagName('div'):
            #    if e.hasAttribute("class"):
            #        if "error" in e.getAttributeNode('class').nodeValue:
            #           print(e)
            #        else:
            #           print(e)
            if not renderedPage:
                if "Render failed" in stats:
                    stats['Render failed'] += 1
                else:
                    stats['Render failed'] = 1
                if stdout:
                    print("\n%s" % page['url'])
                cnt_err += 1
                result.insert(-1, page['url'])
                data[page] = pages[page]
                continue
            if renderedPage.find('<div class="error">') > 0:
                t = re.findall('<div class="error">(.*?)</div>', renderedPage, re.IGNORECASE|re.MULTILINE)
                for x in t:
                    print("\n    %s" % t)
                    if x not in stats:
                        stats[x] = 1
                    else:
                        stats[x] += 1
                if stdout:
                    print("\n%s" % pages[page])
                cnt_err += 1
                result.insert(-1, pages[page])
                data[page] = pages[page]
            elif stdout:
                print("\r [%s/%s]" % (cnt_err, cnt), end='')

        json.dump(data, open('pages.json', 'w+'),  indent=1)

        if stdout:
            print("-- stats --")
            for x in stats:
                print("'%s' : %s" % (x, stats[x]))
        return result
