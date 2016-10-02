#
# Things to do before uploading themes
# 1) Make sure all themes are in mp3 format
# 2) Remove all tags etc from the mp3 file
# 3) Generate Replay Gain for each file
#
import sys
import os
import re
import urllib2
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import traceback


def isVideoFile(filename):
    if filename.endswith('.mp4'):
        return True
    if filename.endswith('.mkv'):
        return True
    if filename.endswith('.avi'):
        return True
    if filename.endswith('.mov'):
        return True
    return False


# Return a pretty-printed XML string for the Element.
def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    uglyXml = reparsed.toprettyxml(indent="    ")
    text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
    return text_re.sub('>\g<1></', uglyXml)


class InfoXml():
    def __init__(self, tvdb_api_key='2B8557E0CBF7D720', tmdb_api_key='f7f51775877e0bb6703520952b3c7840'):
        self.tvdb_api_key = tvdb_api_key
        self.tvdb_url_prefix = 'http://thetvdb.com/api'
        self.lang = 'en'
        self.tmdb_api_key = tmdb_api_key
        self.tmdb_url_prefix = 'http://api.themoviedb.org/3'
        self.imdb_url_prefix = 'http://www.omdbapi.com/'

    def generateTvShowInfo(self, showId, dir):
        infoFilename = os.path.join(dir, 'info.xml')

        # Check if the XML file already exists
        if os.path.isfile(infoFilename):
            return self._readInfoXml(infoFilename)

        # Get the information for this TV Show
        (tvdbId, imdbId, name) = self.getTVDB_info(showId)

        # Check if we have an imdb id, but not a name
        if (imdbId not in [None, ""]) and (name in [None, ""]):
            # Now try searching imdb for the tv show
            (name, year) = self.getIMDB_name_by_id(imdbId)

        # Check to see if a match was found
        if (tvdbId not in [None, ""]) or (imdbId not in [None, ""]) or (name not in [None, ""]):
            # Construct the XML handler
            root = ET.Element('info')
            if tvdbId not in [None, ""]:
                tvdbElem = ET.SubElement(root, 'tvdb')
                tvdbElem.text = tvdbId
            if imdbId not in [None, ""]:
                imdbElem = ET.SubElement(root, 'imdb')
                imdbElem.text = imdbId
            if name not in [None, ""]:
                nameElem = ET.SubElement(root, 'name')
                nameElem.text = name

            # Now create the file for the Store
            fileContent = prettify(root)

            try:
                recordFile = open(infoFilename, 'w')
                recordFile.write(fileContent.encode('utf-8'))
                recordFile.close()
            except:
                print "Error: Failed to write %s" % showId
                print traceback.format_exc()
                if os.path.isfile(infoFilename):
                    os.remove(infoFilename)
                sys.exit(2)

        else:
            print "No data found for TV Show %s" % showId
            # for delFile in os.listdir(dir):
            #     os.remove(os.path.join(dir, delFile))
            # os.rmdir(dir)

        return (tvdbId, imdbId, name)

    def generateMovieInfo(self, movieId, dir):
        infoFilename = os.path.join(dir, 'info.xml')

        # Check if the XML file already exists
        if os.path.isfile(infoFilename):
            return self._readInfoXml(infoFilename)

        # Get the information for this TV Show
        (tmdbId, imdbId, name) = self.getTMDB_info(movieId)

        if (tmdbId in [None, ""]) or (imdbId in [None, ""]) or (name in [None, ""]):
            # Now try searching imdb for the movie
            (name, year) = self.getIMDB_name_by_id(movieId)

            if name not in [None, ""]:
                # Found the name, so the imdb number must be OK
                imdbId = movieId
                # Now do a lookup using the name back on TMDB
                tmdbId = self.getTMDB_by_name(name, year)

        # Check to see if a match was found
        if (tmdbId not in [None, ""]) and (imdbId not in [None, ""]) and (name not in [None, ""]):
            # Construct the XML handler
            root = ET.Element('info')
            if tmdbId not in [None, ""]:
                tvdbElem = ET.SubElement(root, 'tmdb')
                tvdbElem.text = tmdbId
            if imdbId not in [None, ""]:
                imdbElem = ET.SubElement(root, 'imdb')
                imdbElem.text = imdbId
            if name not in [None, ""]:
                nameElem = ET.SubElement(root, 'name')
                nameElem.text = name

            # Now create the file for the Store
            fileContent = prettify(root)

            try:
                recordFile = open(infoFilename, 'w')
                recordFile.write(fileContent.encode('utf-8'))
                recordFile.close()
            except:
                print "Error: Failed to write %s" % movieId
                print traceback.format_exc()
                if os.path.isfile(infoFilename):
                    os.remove(infoFilename)
                sys.exit(2)
        else:
            print "No data found for Movie %s" % movieId

        return (tmdbId, imdbId, name)

    # Get the imdb id from the tvdb id
    def getTVDB_info(self, id):
        # http://thetvdb.com/api/2B8557E0CBF7D720/series/75565/en.xml
        url = '%s/%s/series/%s/en.xml' % (self.tvdb_url_prefix, self.tvdb_api_key, id)
        resp_details = self._makeCall(url)

        tvdbId = None
        imdbId = None
        name = None
        # The response is XML
        if resp_details not in [None, ""]:
            respData = ET.ElementTree(ET.fromstring(resp_details))

            rootElement = respData.getroot()
            if rootElement not in [None, ""]:
                if rootElement.tag == 'Data':
                    series = rootElement.findall('Series')
                    # Only want to process anything if there is just a single series
                    if (series not in [None, ""]) and (len(series) > 0):
                        # There should only be one series as we selected by Id
                        selectedSeries = series[0]

                        if selectedSeries not in [None, ""]:
                            tvdbIdElem = selectedSeries.find('id')
                            if tvdbIdElem not in [None, ""]:
                                tvdbId = tvdbIdElem.text
                            imdbIdElem = selectedSeries.find('IMDB_ID')
                            if imdbIdElem not in [None, ""]:
                                imdbId = imdbIdElem.text
                            nameElem = selectedSeries.find('SeriesName')
                            if nameElem not in [None, ""]:
                                name = nameElem.text

        return (tvdbId, imdbId, name)

    def getTMDB_info(self, id):
        url = "%s/%s/%s?api_key=%s" % (self.tmdb_url_prefix, 'movie', id, self.tmdb_api_key)
        json_details = self._makeCall(url)

        tmdb_id = None
        imdb_id = None
        name = None
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)

            # The results of the search come back as an array of entries
            if 'id' in json_response:
                tmdb_id = json_response.get('id', None)
                if tmdb_id not in [None, ""]:
                    tmdb_id = str(tmdb_id)

            if 'imdb_id' in json_response:
                imdb_id = json_response.get('imdb_id', None)
                if imdb_id not in [None, ""]:
                    imdb_id = str(imdb_id)

            if 'title' in json_response:
                name = json_response.get('title', None)

        return (tmdb_id, imdb_id, name)

    # Get the ID from imdb
    def getIMDB_name_by_id(self, id):
        url = "%s?i=%s" % (self.imdb_url_prefix, id)
        json_details = self._makeCall(url)

        name = None
        year = None
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)

            if json_response.get('Response', 'False') == 'True':
                if 'imdbID' in json_response:
                    imdb_id = json_response.get('imdbID', None)
                    if imdb_id not in [None, ""]:
                        # Make sure we actually got the value we asked for
                        if str(imdb_id) == id:
                            if 'Title' in json_response:
                                name = json_response.get('Title', None)
                            if 'Year' in json_response:
                                year = json_response.get('Year', None)
        return (name, year)

    def getTMDB_by_name(self, name, year=''):
        clean_name = urllib2.quote(self.__clean_name(name))
        url = "%s/%s?language=%s&api_key=%s&query=%s" % (self.tmdb_url_prefix, 'search/movie', self.lang, self.tmdb_api_key, clean_name)
        json_details = self._makeCall(url)

        id = None
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)

            # The results of the search come back as an array of entries
            if 'results' in json_response:
                no_year_results = []
                year_match_results = []
                for result in json_response['results']:
                    id = result.get('id', None)
                    if id not in [None, ""]:
                        id = str(id)
                        release_date = result.get('release_date', '')
                        if (year not in [None, '']) and (year in release_date):
                            year_match_results.append(id)
                        else:
                            no_year_results.append(id)

                if len(year_match_results) > 0:
                    if len(year_match_results) == 1:
                        id = year_match_results[0]
                elif len(no_year_results) == 1:
                    id = no_year_results[0]

        return id

    # Perform the API call
    def _makeCall(self, url):
        resp_details = None
        try:
            req = urllib2.Request(url)
            req.add_header('Accept', 'application/json')
            response = urllib2.urlopen(req)
            resp_details = response.read()
            try:
                response.close()
            except:
                pass
        except:
            pass

        return resp_details

    def __clean_name(self, mystring):
        newstring = ''
        for word in mystring.split(' '):
            if word.isalnum() is False:
                w = ""
                for i in range(len(word)):
                    if(word[i].isalnum()):
                        w += word[i]
                word = w
            newstring += ' ' + word
        return newstring.strip().encode('utf-8')

    def _readInfoXml(self, infoFilename):
        # Create an XML parser
        infoXmlTree = ET.ElementTree(file=infoFilename)
        infoXmlRoot = infoXmlTree.getroot()

        tmdb = None
        imdb = None
        name = None
        tvdb = None

        tmdbElm = infoXmlRoot.find('tmdb')
        if tmdbElm not in [None, ""]:
            tmdb = tmdbElm.text

        imdbElm = infoXmlRoot.find('imdb')
        if imdbElm not in [None, ""]:
            imdb = imdbElm.text

        nameElm = infoXmlRoot.find('name')
        if nameElm not in [None, ""]:
            name = nameElm.text

        tvdbElm = infoXmlRoot.find('tvdb')
        if tvdbElm not in [None, ""]:
            tvdb = tvdbElm.text

        # Check if we have an imdb value and no name, we should be able
        # to have a name if we have an imdb value
        if (imdb not in [None, ""]) and (name in [None, ""]):
            print "No Name when imdb id present for %s" % infoFilename
            sys.exit(2)

        # Make sure the data has wither a tv or movie Id
        if tmdb not in [None, ""]:
            return (tmdb, imdb, name)
        elif tvdb not in [None, ""]:
            return (tvdb, imdb, name)
        else:
            print "Incomplete info file %s" % infoFilename
            sys.exit(2)


##################################
# Main of the TvTunes Service
##################################
if __name__ == '__main__':
    print "About to generate tvtunes-store.xml"

    shouldOpenWindows = False

    # Construct the XML handler
    root = ET.Element('tvtunesStore')
    enabledElem = ET.SubElement(root, 'enabled')
    enabledElem.text = "true"
    tvshowsElem = ET.SubElement(root, 'tvshows')
    moviesElem = ET.SubElement(root, 'movies')

    # Now add each tv show into the list
    tvShowIds = []
    if os.path.exists('tvshows'):
        tvShowIds = os.listdir('tvshows')

    print "Number of TV Shows is %d" % len(tvShowIds)
    openWindows = 0

    infoXml = InfoXml()

    for tvShowId in tvShowIds:
        # Get the contents of the directory
        themesDir = "%s/%s" % ('tvshows', tvShowId)
        themes = os.listdir(themesDir)

        # Remove any info.xml files
        if 'info.xml' in themes:
            themes.remove('info.xml')

        # Make sure the themes are not empty
        if len(themes) < 1:
            print "No themes in directory: %s" % themesDir
            continue

        # Generate the XML for the given TV Show
        (tvdbId, imdbId, name) = infoXml.generateTvShowInfo(tvShowId, themesDir)

        if tvdbId in [None, ""]:
            print "Skipping %s as no ID information" % themesDir
            continue

        # Create an element for this tv show
        tvshowElem = ET.SubElement(tvshowsElem, 'tvshow')
        tvshowElem.attrib['id'] = tvShowId
        if tvdbId not in [None, ""]:
            tvshowElem.attrib['tvdb'] = tvdbId
        if imdbId not in [None, ""]:
            tvshowElem.attrib['imdb'] = imdbId

        numThemes = 0
        # Add each theme to the element
        for theme in themes:
            fullThemePath = "%s/%s" % (themesDir, theme)
            # Get the size of this theme file
            statinfo = os.stat(fullThemePath)
            fileSize = statinfo.st_size
            # Make sure not too small
            if fileSize < 19460:
                print "Themes file %s/%s is very small" % (themesDir, theme)
                continue

            themeElem = None
            # Add the theme to the list
            if isVideoFile(theme):
                # print "Video Theme for %s is %s" % (themesDir, theme)
                themeElem = ET.SubElement(tvshowElem, 'videotheme')
            else:
                numThemes = numThemes + 1
                if not theme.endswith('.mp3'):
                    print "Audio theme %s is not mp3: %s" % (themesDir, theme)
                themeElem = ET.SubElement(tvshowElem, 'audiotheme')
            themeElem.text = theme
            themeElem.attrib['size'] = str(fileSize)

        if numThemes > 1:
            print "TvShow %s has %d themes" % (themesDir, numThemes)
            if shouldOpenWindows and (openWindows < 10):
                windowsDir = "start %s\\%s" % ('tvshows', tvShowId)
                os.system(windowsDir)
                openWindows = openWindows + 1

    # Now add each tv show into the list
    movieIds = []
    if os.path.exists('movies'):
        movieIds = os.listdir('movies')

    print "Number of Movies is %d" % len(movieIds)

    for movieId in movieIds:
        # Get the contents of the directory
        themesDir = "%s/%s" % ('movies', movieId)
        themes = os.listdir(themesDir)

        # Remove any info.xml files
        if 'info.xml' in themes:
            themes.remove('info.xml')

        # Make sure the themes are not empty
        if len(themes) < 1:
            print "No themes in directory: %s" % themesDir
            continue

        # Generate the XML for the given TV Show
        (tmdbId, imdbId, name) = infoXml.generateMovieInfo(movieId, themesDir)

        if (tmdbId in [None, ""]) or (imdbId in [None, ""]):
            print "Skipping %s as no ID information" % themesDir
            continue

        # Create an element for this tv show
        movieElem = ET.SubElement(moviesElem, 'movie')
        # The id is actually the name of the directory
        movieElem.attrib['id'] = movieId
        movieElem.attrib['tmdb'] = tmdbId
        movieElem.attrib['imdb'] = imdbId

        numThemes = 0
        # Add each theme to the element
        for theme in themes:
            fullThemePath = "%s/%s" % (themesDir, theme)
            # Get the size of this theme file
            statinfo = os.stat(fullThemePath)
            fileSize = statinfo.st_size
            # Make sure not too small
            if fileSize < 19460:
                print "Themes file %s/%s is very small" % (themesDir, theme)
                continue

            themeElem = None
            # Add the theme to the list
            if isVideoFile(theme):
                if fileSize > 104857600:
                    print "Themes file %s/%s is very large" % (themesDir, theme)
                    continue
                # print "Video Theme for %s is %s" % (themesDir, theme)
                themeElem = ET.SubElement(movieElem, 'videotheme')
            else:
                if fileSize > 20971520:
                    print "Themes file %s/%s is very large" % (themesDir, theme)
                    continue
                numThemes = numThemes + 1
                if not theme.endswith('.mp3'):
                    print "Audio theme %s is not mp3: %s" % (themesDir, theme)
                themeElem = ET.SubElement(movieElem, 'audiotheme')
            themeElem.text = theme
            themeElem.attrib['size'] = str(fileSize)

        if numThemes > 1:
            print "Movie %s has %d themes" % (themesDir, numThemes)
            if shouldOpenWindows and (openWindows < 10):
                windowsDir = "start %s\\%s" % ('movies', movieId)
                os.system(windowsDir)
                openWindows = openWindows + 1

    del infoXml

    # Now create the file for the Store
    fileContent = prettify(root)

    recordFile = open('tvtunes-store.xml', 'w')
    recordFile.write(fileContent)
    recordFile.close()
