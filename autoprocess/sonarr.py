import sys
import os
import logging
import time


def processEpisode(dirName, settings, nzbGet=False, logger=None):

    if nzbGet:
        errorprefix = "[ERROR] "
        infoprefix = "[INFO] "
    else:
        errorprefix = ""
        infoprefix = ""

    log = logger or logging.getLogger(__name__)

    log.info("%sSonarr notifier started." % infoprefix)

    # Import Requests
    try:
        import requests
    except ImportError:
        log.exception("%sPython module REQUESTS is required. Install with 'pip install requests' then try again." % errorprefix)
        log.error("%sPython executable path is %s" % (errorprefix, sys.executable))
        return False

    host = settings.Sonarr['host']
    port = settings.Sonarr['port']
    apikey = settings.Sonarr['apikey']

    if apikey == '':
        log.error("%sYour Sonarr API Key can not be blank. Update autoProcess.ini." % errorprefix)
        return False

    try:
        ssl = int(settings.Sonarr['ssl'])
    except:
        ssl = 0
    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"

    webroot = settings.Sonarr['webroot']
    url = protocol + host + ":" + str(port) + webroot + "/api/command"
    payload = {'name': 'downloadedepisodesscan', 'path': dirName}
    headers = {'X-Api-Key': apikey}

    log.debug("Sonarr host: %s." % host)
    log.debug("Sonarr port: %s." % port)
    log.debug("Sonarr webroot: %s." % webroot)
    log.debug("Sonarr apikey: %s." % apikey)
    log.debug("Sonarr protocol: %s." % protocol)
    log.debug("URL '%s' with payload '%s.'" % (url, payload))

    log.info("%sRequesting Sonarr to scan directory '%s'." % (infoprefix, dirName))
    return accessAPI(url, payload, headers, log, requests, nzbGet)


def accessAPI(url, payload, headers, log, requests, nzbGet, sleep=10, retry=0, maxretry=5):
    try:
        if nzbGet:
            errorprefix = "[ERROR] "
            infoprefix = "[INFO] "
        else:
            errorprefix = ""
            infoprefix = ""

        r = requests.post(url, json=payload, headers=headers)
        rstate = r.json()
        log.debug(rstate)
        log.info("%sSonarr response: %s." % (infoprefix, rstate['state']))
        if rstate['body']['path'] != payload['path']:
            if retry > maxretry:
                log.error("Sonarr returned path %s that does not match the directory that was requested to be scanned %s. Maximum number of retries exceeded (%d)." % (rstate['body']['path'], payload['path'], maxretry))
                return False
            log.error("Sonarr returned path %s that does not match the directory that was requested to be scanned %s. Trying again in %d seconds." % (rstate['body']['path'], payload['path'], sleep))
            time.sleep(sleep)
            return accessAPI(url, payload, headers, log, requests, nzbGet, retry=(retry + 1))
        return True
    except:
        log.exception("%sUpdate to Sonarr failed, check if Sonarr is running, autoProcess.ini settings and make sure your Sonarr settings are correct (apikey?), or check install of python modules requests." % errorprefix)
        return False
