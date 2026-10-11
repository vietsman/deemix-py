import json
from copy import deepcopy
from os import makedirs
from pathlib import Path

from deezer import TrackFormats

import deemix.utils.localpaths as localpaths


class OverwriteOption:
    """Should the lib overwrite files?"""

    OVERWRITE = 'y'
    DONT_OVERWRITE = 'n'
    DONT_CHECK_EXT = 'e'
    KEEP_BOTH = 'b'
    ONLY_TAGS = 't'


class FeaturesOption:
    """What should I do with featured artists?"""

    NO_CHANGE = "0"
    REMOVE_TITLE = "1"
    REMOVE_TITLE_ALBUM = "3"
    MOVE_TITLE = "2"


DEFAULT_TAGS = {
    "title": True,
    "artist": True,
    "artists": True,
    "album": True,
    "cover": True,
    "trackNumber": True,
    "trackTotal": False,
    "discNumber": True,
    "discTotal": False,
    "albumArtist": True,
    "genre": True,
    "year": True,
    "date": True,
    "explicit": False,
    "isrc": True,
    "length": True,
    "barcode": True,
    "bpm": True,
    "replayGain": False,
    "label": True,
    "lyrics": False,
    "syncedLyrics": False,
    "copyright": False,
    "composer": False,
    "involvedPeople": False,
    "source": False,
    "rating": False,
    "savePlaylistAsCompilation": False,
    "useNullSeparator": False,
    "saveID3v1": True,
    "multiArtistSeparator": "default",
    "singleAlbumArtist": False,
    "coverDescriptionUTF8": False,
}

DEFAULTS = {
    "downloadLocation": str(localpaths.getMusicFolder()),
    "tracknameTemplate": "%artist% - %title%",
    "albumTracknameTemplate": "%tracknumber% - %title%",
    "playlistTracknameTemplate": "%position% - %artist% - %title%",
    "createPlaylistFolder": True,
    "playlistNameTemplate": "%playlist%",
    "createArtistFolder": False,
    "artistNameTemplate": "%artist%",
    "createAlbumFolder": True,
    "albumNameTemplate": "%artist% - %album%",
    "createCDFolder": True,
    "createStructurePlaylist": False,
    "createSingleFolder": False,
    "padTracks": True,
    "paddingSize": "0",
    "illegalCharacterReplacer": "_",
    "queueConcurrency": 3,
    "maxBitrate": str(TrackFormats.MP3_320),
    "feelingLucky": False,
    "fallbackBitrate": False,
    "fallbackSearch": False,
    "fallbackISRC": False,
    "logErrors": True,
    "logSearched": False,
    "overwriteFile": OverwriteOption.DONT_OVERWRITE,
    "createM3U8File": False,
    "playlistFilenameTemplate": "playlist",
    "syncedLyrics": False,
    "embeddedArtworkSize": 800,
    "embeddedArtworkPNG": False,
    "localArtworkSize": 1400,
    "localArtworkFormat": "jpg",
    "saveArtwork": True,
    "coverImageTemplate": "cover",
    "saveArtworkArtist": False,
    "artistImageTemplate": "folder",
    "jpegImageQuality": 90,
    "dateFormat": "Y-M-D",
    "albumVariousArtists": True,
    "removeAlbumVersion": False,
    "removeDuplicateArtists": True,
    "featuredToTitle": FeaturesOption.NO_CHANGE,
    "titleCasing": "nothing",
    "artistCasing": "nothing",
    "executeCommand": "",
    "tags": deepcopy(DEFAULT_TAGS),
}


def _coerce_settings(raw_settings):
    if raw_settings is None:
        raw_settings = {}

    settings = deepcopy(DEFAULTS)
    if isinstance(raw_settings, dict):
        settings.update(raw_settings)
        tags = raw_settings.get('tags', {})
        if isinstance(tags, dict):
            settings['tags'] = deepcopy(DEFAULT_TAGS)
            settings['tags'].update(tags)

    if not settings.get('downloadLocation'):
        settings['downloadLocation'] = DEFAULTS['downloadLocation']

    for template in [
        'tracknameTemplate',
        'albumTracknameTemplate',
        'playlistTracknameTemplate',
        'playlistNameTemplate',
        'artistNameTemplate',
        'albumNameTemplate',
        'playlistFilenameTemplate',
        'coverImageTemplate',
        'artistImageTemplate',
    ]:
        if not settings.get(template):
            settings[template] = DEFAULTS[template]

    return settings


def save(settings, configFolder=None):
    configFolder = Path(configFolder or localpaths.getConfigFolder())
    makedirs(configFolder, exist_ok=True)
    with open(configFolder / 'config.json', 'w', encoding='utf-8') as configFile:
        json.dump(_coerce_settings(settings), configFile, indent=2)


def load(configFolder=None):
    configFolder = Path(configFolder or localpaths.getConfigFolder())
    makedirs(configFolder, exist_ok=True)
    if not (configFolder / 'config.json').is_file():
        save(DEFAULTS, configFolder)

    with open(configFolder / 'config.json', 'r', encoding='utf-8') as configFile:
        try:
            settings = json.load(configFile)
        except json.decoder.JSONDecodeError:
            save(DEFAULTS, configFolder)
            settings = deepcopy(DEFAULTS)
        except Exception:
            settings = deepcopy(DEFAULTS)

    normalized = _coerce_settings(settings)
    if normalized != settings:
        save(normalized, configFolder)
        return normalized
    return normalized


def check(settings):
    normalized = _coerce_settings(settings)
    return 1 if normalized != settings else 0
