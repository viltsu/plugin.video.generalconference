# -*- coding: UTF-8 -*-
import os
import sys
import urlparse
import re
import urllib
import urllib2
import xbmcgui
import xbmcplugin
import xbmcaddon
import string

try:
    import StorageServer
    StorageServer = StorageServer
except ImportError, e:
    import storageserverdummy as StorageServer

BASE_URL = 'http://www.lds.org'
CONFERENCES_URL = BASE_URL + '/general-conference/conferences?lang=eng&clang='
SESSIONS_URL = BASE_URL + '/general-conference/sessions/'
USER_AGENT = 'Mozilla/5.0 (compatible, XBMC addon)'
AMF_URL = 'http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAAAjP0hvGE~,N-ZbNsw4qBrgc4nqHfwj6D_S8kJzTvbq'
LIVE_URL = 'http://c.brightcove.com/services/mobile/streaming/index/rendition.m3u8'


class conferenceAddon(object):
    def __init__(self,  handle, path, addon):
        self.handle = handle
        self.path = path
        self.localized = addon.getLocalizedString
        self.icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
        self.fanart = os.path.join(addon.getAddonInfo('path'), 'fanart.jpg')
        self.cache = StorageServer.StorageServer(addon.getAddonInfo('id'), 24)
        self.videoq = ['video-360p', 'video-720p', 'video-1080p'][int(addon.getSetting('video_quality'))]
        self.videol = ['eng', 'fin'][int(addon.getSetting('video_language'))]
        self.last = [1995, 2011][int(addon.getSetting('video_language'))]
        self.postData = os.path.join(addon.getAddonInfo('path'), 'resources', 'req')

    def showConferences(self):
        # self._addLink(self.localized(30002), {'live': 1})
        html = self._downloadUrl(CONFERENCES_URL + self.videol)
        for m in re.finditer("<li><a href=\"http://www.lds.org/general-conference/sessions/([^\"]+)\">([^<]+)</a></li>", html):
            year = m.group(1)[0:4]
            if int(year) < self.last:
                continue
            confurl = SESSIONS_URL + m.group(1)
            title = year + ' ' + m.group(2)
            self._addDirectory(title, {'url': confurl,  'cid': title})
        xbmcplugin.endOfDirectory(self.handle)

    def showConference(self,  cid,  url):
        cachekey = cid + self.videol + self.videoq
        store = self.cache.get(cachekey)
        html = self._downloadUrl(url).replace('\n', '')
        store = []
        for m in re.finditer("<table class=\"sessions\" id=\"([^\"]+)\">(.*?)</table>", html):
            sessionHtml = m.group(2)
            sessionTitle = self._search("<session value=\"[^\"]+\">([^<]+)</session>", sessionHtml) or \
                           self._search("<h2>([^<]+)</h2>", sessionHtml) or \
                           "-"
            speakers = []
            for n in re.finditer("<span class=\"talk\">(.*?)</span>.*?<span class=\"speaker\">([^<]*)</span>.*?<div class=\"download-menu\">(.*?)</div>",  sessionHtml):
                topic = self._search("<a href[^>]+>([^<]+)</a>", n.group(1)) or "-"
                videoUrl = self._search("<a href=\"([^\"]+)\" class=\"" + self.videoq + "\"", n.group(3)) or \
                           self._search("<a href=\"([^\"]+)\" class=\"(video-360p|video-mp4|video-wmv)\"", n.group(3))
                if videoUrl:
                    speakers.append((topic, n.group(2), videoUrl))
            part = self._search("<td class=\"download\">(.*?)</td>", sessionHtml)
            allUrl = self._search("<a href=\"([^\"]+)\" class=\"" + self.videoq + "\"", part) or \
                     self._search("<a href=\"([^\"]+)\" class=\"(video-360p|video-mp4|video-wmv)\"", part)
            if len(speakers) > 0 or allUrl != None:
                store.append((m.group(1), sessionTitle, speakers, allUrl))
        self.cache.set(cachekey,  repr(store))
        for session, title, talks,  playallurl in store:
            self._addDirectory(title, {'cid': cid,  'sid': session})
        xbmcplugin.endOfDirectory(self.handle)

    def showSession(self,  cid,  sid):
        cachekey = cid + self.videol + self.videoq
        try:
            store = eval(self.cache.get(cachekey))
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok("Error", " If this is first time after installing the plugin \n pleace restart the xbmc.")
            raise SystemExit
        first = True
        for session, title, talks, playallurl in store:
            if sid != session:
                continue
            if first and playallurl:
                self._addLink(self.localized(30001),  {'vid': playallurl})
            for talk in talks:
                topic, talker, videourl = talk
                self._addLink(talker + " - " + topic,  {'vid': videourl})
            first = False
        xbmcplugin.endOfDirectory(self.handle)

    def playVideo(self, vid):
        item = xbmcgui.ListItem(path=vid)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def removeNonPrintable(self, s):
        return filter(lambda x: x in string.printable, s)

    def playLive(self):
        data = open(self.postData, 'rb')
        r = urllib2.Request(AMF_URL, data=data)
        r.add_header('Content-Type', 'application/x-amf')
        r.add_header('Content-Length', '150')
        u = urllib2.urlopen(r)
        content = self.removeNonPrintable(u.read())
        u.close()
        for m in re.finditer(LIVE_URL + "\?assetId=([0-9]*)", content):
            url = LIVE_URL + '?assetId=' + m.group(1)
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)

    def _addLink(self,  title, urlparams,  thumb='DefaultVideo.png'):
        item = xbmcgui.ListItem(title, iconImage=self.icon,  thumbnailImage=thumb)
        item.setProperty('Fanart_Image', self.fanart)
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='video', infoLabels={
            'title': title
            })
        url = self.path + '?' + urllib.urlencode(urlparams)
        xbmcplugin.addDirectoryItem(self.handle, url, item)

    def _addDirectory(self,  title, urlparams,  thumb='DefaultFolder.png'):
        item = xbmcgui.ListItem(title, iconImage=self.icon,  thumbnailImage=thumb)
        item.setProperty('Fanart_Image', self.fanart)
        item.setInfo(type='video', infoLabels={
            'title': title
            })
        url = self.path + '?' + urllib.urlencode(urlparams)
        xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder=True)

    def _downloadUrl(self, url):
        r = urllib2.Request(url.replace('&amp;', '&'))
        r.add_header('User-Agent', USER_AGENT)
        u = urllib2.urlopen(r)
        contents = u.read()
        u.close()
        return contents

    def _search(self, needle, hay):
        r = re.search(needle, hay)
        if not r:
            return None
        return r.group(1)

if __name__ == '__main__':
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])
    conference = conferenceAddon(
                                int(sys.argv[1]),
                                sys.argv[0],
                                xbmcaddon.Addon(id='plugin.video.generalconference'),
                        )
    if 'vid' in PARAMS:
        conference.playVideo(urllib.unquote_plus(PARAMS['vid'][0]))
    elif 'sid' in PARAMS:
        conference.showSession(urllib.unquote_plus(PARAMS['cid'][0]), urllib.unquote_plus(PARAMS['sid'][0]))
    elif 'url' in PARAMS:
        conference.showConference(urllib.unquote_plus(PARAMS['cid'][0]), urllib.unquote_plus(PARAMS['url'][0]))
    elif 'live' in PARAMS:
        conference.playLive()
    else:
        conference.showConferences()
