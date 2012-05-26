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
        self.last = [1995, 2011][int(addon.getSetting('video_language'))]

    def showConferences(self):
        html = self._downloadUrl(CONFERENCES_URL + self.videol)	        
        for m in re.finditer("<li><a href=\"http://www.lds.org/general-conference/sessions/([^\"]+)\">([^<]+)</a></li>", html):
            year = m.group(1)[0:4]
            if int(year) < self.last:
                continue
            confurl = SESSIONS_URL + m.group(1)
            title = year + ' ' + m.group(2)
            self._addDirectory(title, {'url' :confurl,  'cid':title})
        xbmcplugin.endOfDirectory(self.handle)

    def showConference(self,  cid,  url):
        confurl = url
        cachekey = cid + self.videol + self.videoq
        store = self.cache.get(cachekey)
        html = self._downloadUrl(url).replace('\n', '')
        store = {}
        for m in re.finditer("<table class=\"sessions\" id=\"([^\"]+)\">(.*?)</table>", html):
            sessionHtml = m.group(2)
            sessionTitle = self._search("<session value=\"[^\"]+\">([^<]+)</session>", sessionHtml) or \
                           self._search("<h2>([^<]+)</h2>", sessionHtml) or \
                           "-"
            speakers = []
            for n in re.finditer("<span class=\"talk\">(.*?)</span>.*?<span class=\"speaker\">([^<]+)</span>.*?<div class=\"download-menu\">(.*?)</div>",  sessionHtml):                
                topic = self._search("<a href[^>]+>([^<]+)</a>", n.group(1)) or "-"
                videoUrl = self._search("<a href=\"([^\"]+)\" class=\""+self.videoq+"\"", n.group(3)) or \
                           self._search("<a href=\"([^\"]+)\" class=\"(video-360p|video-mp4|video-wmv)\"", n.group(3))
                if videoUrl:
                    speakers.append((topic, n.group(2), videoUrl)) #Topic, Speaker, videoUrl
            part = self._search("<td class=\"download\">(.*?)</td>", sessionHtml)
            allUrl = self._search("<a href=\"([^\"]+)\" class=\""+self.videoq+"\"", part) or \
                     self._search("<a href=\"([^\"]+)\" class=\"(video-360p|video-mp4|video-wmv)\"", part)
            if len(speakers) > 0 or allUrl != None:
                store[m.group(1)] = (sessionTitle, speakers, allUrl) #Session Id, Session title, speakers, Play all url
                self._addDirectory(sessionTitle, {'cid':cid,  'sid':m.group(1)})
        self.cache.set(cachekey,  repr(store))
        xbmcplugin.endOfDirectory(self.handle)
    
    def showSession(self,  cid,  sid):
        cachekey = cid + self.videol + self.videoq
        try:
            store = eval(self.cache.get(cachekey))
            title, talks, playAllUrl = store[sid]
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok("Error", " If this is first time after installing the plugin \n place restart the xbmc.")
            return
        self._addVideo(self.localized(30001),  {'vid':playAllUrl})
        for topic,  talker,  videoUrl in talks:
             self._addVideo(talker + " - " + topic,  {'vid': videoUrl})
        xbmcplugin.endOfDirectory(self.handle)

    def playVideo(self, vid):
        item = xbmcgui.ListItem(path = vid)
        xbmcplugin.setResolvedUrl(self.handle, True, item)
        
    def _search(self, needle, hay):
        r = re.search(needle, hay)
        if not r:
            return None
        return r.group(1)

    def _addVideo(self,  title, urlparams,  thumb = 'DefaultVideo.png'):
        self._addLine(title,  urlparams,  thumb,  True)
        
    def _addDirectory(self,  title, urlparams,  thumb = 'DefaultFolder.png'):
        self._addLine(title,  urlparams,  thumb,  False)
        
    def _addLine(self, title,  urlparams,  thumb,  isPlayable):
        item = xbmcgui.ListItem(title, iconImage = self.icon,  thumbnailImage=thumb)
        item.setProperty('Fanart_Image', self.fanart)
        item.setInfo(type='video', infoLabels={'title': title })
        url = self.path + '?' + urllib.urlencode(urlparams)
        if isPlayable:
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(self.handle, url, item)
        else:
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
