import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.generalconference')
__language__ = __settings__.getLocalizedString
videoq = ['video-360p', 'video-720p', 'video-1080p'][int(__settings__.getSetting('video_quality'))]
videol = ['eng', 'fin'][int(__settings__.getSetting('video_language'))]
onlytalks = __settings__.getSetting('only_talks') == "true"
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )

print str(onlytalks)

def conferences():
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request('http://www.lds.org/general-conference/conferences?lang=eng&clang='+videol,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = items = soup.findAll('ul',attrs={'class':'archive-by-month-list'})[0]('li')
        for i in items:
            #addDir(i.img['alt'],i.a['href'],1,'http://www.lds.org' + i.img['src'], '') 
            addDir(i.img['alt'],i.a['href'],1,'', '') 
        
def sessions(url,iconimage):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.findAll('session')
        for i in items:
            try:
                addDir(i.string.encode('utf-8'),url,2, '', i['value'])
            except:
                pass

def speakers(url,  session):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.findAll('table',attrs={'id':session})[0]('tr')
        try:
            url = items[1]('a', attrs={'class':videoq})[0]['href']
            addLink('Play all', url,  '','',  3, '')
        except:
            pass
        count = 0
        for i in items:
            if count < 2:
                count += 1
                continue
            if onlytalks and i('span')[0]['class'] == 'song':
                continue
            try:
                name =  i('span')[0].a.string.encode('utf-8') + ' - ' +  i('span')[1].string.encode('utf-8')
                url = i('a', attrs={'class':videoq})[0]['href']
                addLink(name,  url,  name, '',   3,  '')
            except:
                pass

def playVideo(url):
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param


def addLink(name,url,description,date,mode,iconimage):
        try:
            description = description + "\n \n Published: " + date
        except:
            description = "Published: " + date
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description } )
        liz.setProperty( "Fanart_Image", fanart )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage, session):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&session="+urllib.quote_plus(session)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    session=urllib.unquote_plus(params["session"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    conferences()

elif mode==1:
    print ""
    sessions(url, iconimage)

elif mode==2:
    print ""
    speakers(url, session)

elif mode==3:
    print ""
    playVideo(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
