# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcaddon

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings
from resources.lib.settings import WindowShowing
from resources.lib.backend import TunesBackend

ADDON = xbmcaddon.Addon(id='script.tvtunes')
CWD = ADDON.getAddonInfo('path').decode("utf-8")
LIB_DIR = xbmc.translatePath(os.path.join(CWD, 'resources', 'lib').encode("utf-8")).decode("utf-8")


# Class to detect when something in the system has changed
class TvTunesMonitor(xbmc.Monitor):
    def onSettingsChanged(self):
        log("TvTunesMonitor: Notification of settings change received")
        Settings.reloadSettings()


##################################
# Main of the TvTunes Service
##################################
if __name__ == '__main__':
    log("Starting TvTunes Service %s" % ADDON.getAddonInfo('version'))

    # Make sure we have recorded this machines Id
    Settings.setTvTunesId()

    # Check if the settings mean we want to reset the volume on startup
    startupVol = Settings.getStartupVolume()

    if startupVol < 0:
        log("TvTunesService: No Volume Change Required")
    else:
        log("TvTunesService: Setting volume to %s" % startupVol)
        xbmc.executebuiltin('SetVolume(%d)' % startupVol, True)

    # Check if the video info button should be hidden, we do this here as this will be
    # called when the system is loaded, it can then be read by the skin
    # when it comes to draw the button
    WindowShowing.updateHideVideoInfoButton()
    WindowShowing.updateShowOnContextMenu()

    # Make sure the user wants to play themes
    if Settings.isThemePlayingEnabled():
        log("TvTunesService: Theme playing enabled")

        # if Settings.isUploadEnabled():
        #    log("TvTunesService: Launching uploader")
        #    xbmc.executebuiltin('RunScript(%s)' % os.path.join(LIB_DIR, "upload.py"), False)
        # else:
        #    log("TvTunesService: Uploader not enabled")

        displayNotice = True
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": { "addonid": "repository.urepo", "properties": ["enabled", "broken", "name", "author"]  }, "id": 1}')
        json_response = json.loads(json_query)

        if ("result" in json_response) and ('addon' in json_response['result']):
            addonItem = json_response['result']['addon']
            if (addonItem['enabled'] is True) and (addonItem['broken'] is False) and (addonItem['type'] == 'xbmc.addon.repository') and (addonItem['addonid'] == 'repository.urepo'):
                displayNotice = False

                # Create a monitor so we can reload the settings if they change
                systemMonitor = TvTunesMonitor()

                # Start looping to perform the TvTune theme operations
                main = TunesBackend()

                # Start the themes running
                main.runAsAService()

                del main
                del systemMonitor

        if displayNotice:
            xbmc.executebuiltin('Notification("URepo Repository Required","www.urepo.org",10000,%s)' % ADDON.getAddonInfo('icon'))
    else:
        log("TvTunesService: Theme playing disabled")
