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
        #self._addDirectory(self.localized(30002), {'live':1})
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
        store = []
        for m in re.finditer("<table.*?<session value=\"([^\"]+)\">([^<]+)</session>(.*?)</table>", html):
            sessionHtml = m.group(3)
            speakers = []
            for n in re.finditer("<tr.*?<span class=\"talk\"><a href.*?>([^<]+)</a></span>.*?<span class=\"speaker\">([^<]+)</span>.*?<li><a href=\"([^\?]+)\?download=true\" class=\""+self.videoq+"\".*?</tr>",  sessionHtml):
                speakers.append((n.group(1) , n.group(2),  n.group(3))) #Topic, Speaker, videoUrl
            if len(speakers) == 0: #try fallback if no match
                for n in re.finditer("<tr.*?<span class=\"talk\"><a href.*?>([^<]+)</a></span>.*?<span class=\"speaker\">([^<]+)</span>.*?<li><a href=\"([^\?]+)\?download=true\" class=\"(video-360p|video-mp4|video-wmv)\".*?</tr>",  sessionHtml):
                    speakers.append((n.group(1) , n.group(2),  n.group(3))) #Topic, Speaker, videoUrl
            o = re.search("<td class=\"download\">(.*?)</td>", sessionHtml)
            p = re.search("<a href=\"([^\"]+)\" class=\""+self.videoq+"\"", o.group(1))
            if not p: #try fallback if no match
                p = re.search("<a href=\"([^\"]+)\" class=\"(video-mp4|video-wmv)\"", o.group(1))
            if not p:
                allUrl = None
            else:
                allUrl = p.group(1)
            if len(speakers) > 0:
                store.append((m.group(1),  m.group(2),  speakers,  allUrl)) #Session Id, Session title, speakers, Play all url
        self.cache.set(cachekey,  repr(store))
        
        for session, title, talks,  playallurl in store:
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
        for session, title, talks, playallurl in store:
            if sid !=  session:
                continue
            if first and playallurl:
                self._addLink(self.localized(30001),  {'vid':playallurl})
            for talk in talks:
                topic,  talker,  videourl=talk
                self._addLink(talker + " - " + topic,  {'vid': videourl})
            first = False
        xbmcplugin.endOfDirectory(self.handle)

    def playVideo(self, vid):
        item = xbmcgui.ListItem(path = vid)
        xbmcplugin.setResolvedUrl(self.handle, True, item)
    
    def playLive(self):
        dialog = xbmcgui.Dialog()
        dialog.ok("Error", "This has not been yet implemeted")
        
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
    elif PARAMS.has_key('live'):
        conference.playLive()
    else:
        conference.showConferences()
