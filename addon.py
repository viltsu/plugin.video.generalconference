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
import xbmc
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

BASE_URL = 'http://www.lds.org'
CONFERENCES_URL = BASE_URL + '/general-conference/conferences?lang=eng&clang='
SESSIONS_URL = BASE_URL + '/general-conference/sessions/'
USER_AGENT = 'Mozilla/5.0 (compatible, XBMC addon)'

class conferenceAddon(object):
    
    def __init__(self,  handle, path, addon):
        self.handle = handle
        self.path = path
        self.localized= addon.getLocalizedString
        self.icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
        self.fanart = os.path.join(addon.getAddonInfo('path'), 'fanart.jpg')
        self.cache = StorageServer.StorageServer(addon.getAddonInfo('id'), 24)
        self.videoq = ['video-360p', 'video-720p', 'video-1080p'][int(addon.getSetting('video_quality'))]
        self.videol = ['eng', 'fin'][int(addon.getSetting('video_language'))]

    def showConferences(self):
        html = self._downloadUrl(CONFERENCES_URL + self.videol)	        
        for m in re.finditer("<li><a href=\"http://www.lds.org/general-conference/sessions/([^\"]+)\"><img src=\"([^\"]+)\"[^>]+>([^<]+)</a></li>", html):
            confurl = SESSIONS_URL + m.group(1)
            thumb = BASE_URL + m.group(2)
            title = m.group(3)
            self._addDirectory(title, {'url' :confurl,  'cid':title}, thumb)
        xbmcplugin.endOfDirectory(self.handle)

    def showConference(self,  cid,  url):
        confurl = url
        cachekey = cid + self.videol + self.videoq
        store = self.cache.get(cachekey)
        if not store:
            html = self._downloadUrl(url).replace('\n', '')
            store = []
            for m in re.finditer("<table.*?<session value=\"([^\"]+)\">([^<]+)</session>.*?<div class=\"download-menu\">.*?<a href=\"([^\"]+)\" class=\""+self.videoq+"\"(.*?)</table>", html):
                sessionHtml = m.group(4)
                speakers = []
                for n in re.finditer("<tr.*?<span class=\"talk\"><a href.*?>([^<]+)</a></span>.*?<span class=\"speaker\">([^<]+)</span>.*?<li><a href=\"([^\?]+)\?download=true\" class=\""+self.videoq+"\".*?</tr>",  sessionHtml):
                    speakers.append((n.group(1) , n.group(2),  n.group(3))) #Topic, Speaker, videoUrl
                store.append((m.group(1),  m.group(2),  speakers,  m.group(3))) #Session Id, Session title, speakers, Play all url
            self.cache.set(cachekey,  repr(store))
        else:
            store = eval(store)
        for i in store:
            session, title, talks,  playallurl = i
            self._addDirectory(title, {'cid':cid,  'sid':session})
        xbmcplugin.endOfDirectory(self.handle)
    
    def showSession(self,  cid,  sid):
        cachekey = cid + self.videol + self.videoq
        try:
            store = eval(self.cache.get(cachekey))
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok("Error", " If this is first time after installing the plugin \n pleace restart the xbmc.")
        first = True
        for i in store:
            session, title,talks,playallurl = i
            if sid !=  session:
                continue
            if first:
                self._addLink(self.localized(30001),  {'vid':playallurl})
                first = False
            for talk in talks:
                topic,  talker,  videourl=talk
                self._addLink(talker + " - " + topic,  {'vid': videourl})
        xbmcplugin.endOfDirectory(self.handle)

    def playVideo(self, vid):
        item = xbmcgui.ListItem(path = vid)
        xbmcplugin.setResolvedUrl(self.handle, True, item)
        
    def _addLink(self,  title, urlparams,  thumb = 'DefaultVideo.png'):
        item = xbmcgui.ListItem(title, iconImage = self.icon,  thumbnailImage=thumb)
        item.setProperty('Fanart_Image', self.fanart)
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='video', infoLabels={
            'title': title
            })
        url = self.path + '?' + urllib.urlencode(urlparams)
        xbmcplugin.addDirectoryItem(self.handle, url, item)
    
    def _addDirectory(self,  title, urlparams,  thumb = 'DefaultFolder.png'):
        item = xbmcgui.ListItem(title, iconImage = self.icon,  thumbnailImage=thumb)
        item.setProperty('Fanart_Image', self.fanart)
        item.setInfo(type='video', infoLabels={
            'title': title
            })
        url = self.path + '?' + urllib.urlencode(urlparams)
        xbmcplugin.addDirectoryItem(self.handle, url, item, isFolder = True)

    def _downloadUrl(self, url):
        r = urllib2.Request(url.replace('&amp;', '&'))
        r.add_header('User-Agent', USER_AGENT)
        u = urllib2.urlopen(r)
        contents = u.read()
        u.close()
        return contents
        
if __name__ == '__main__':
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])
    conference = conferenceAddon(
                                int(sys.argv[1]), 
                                sys.argv[0], 
                                xbmcaddon.Addon(id='plugin.video.generalconference'), 
                        )
    if PARAMS.has_key('vid'):
        conference.playVideo(urllib.unquote_plus(PARAMS['vid'][0]))
    elif PARAMS.has_key('sid'):
        conference.showSession(urllib.unquote_plus(PARAMS['cid'][0]),urllib.unquote_plus(PARAMS['sid'][0]))
    elif PARAMS.has_key('url'):
        conference.showConference(urllib.unquote_plus(PARAMS['cid'][0]),urllib.unquote_plus(PARAMS['url'][0]))
    else:
        conference.showConferences()
