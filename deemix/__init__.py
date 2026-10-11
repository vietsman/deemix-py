#!/usr/bin/env python3
import re
from urllib.request import urlopen

from deemix.itemgen import (
    generateAlbumItem,
    generateArtistDiscographyItem,
    generateArtistItem,
    generateArtistTopItem,
    generatePlaylistItem,
    generateTrackItem,
)
from deemix.errors import LinkNotRecognized, LinkNotSupported

__version__ = "3.6.6"


def normalize_url(link):
    """Normalize Deezer URL input while tolerating malformed values."""
    if not isinstance(link, str):
        return ""

    normalized = link.strip()
    if not normalized:
        return ""

    if "deezer.page.link" in normalized:
        try:
            normalized = urlopen(normalized).url
        except Exception:
            return ""

    for delimiter in ("?", "#", "&"):
        if delimiter in normalized:
            normalized = normalized.split(delimiter, 1)[0]

    return normalized.rstrip("/")


# Returns the Resolved URL, the Type and the ID
def parseLink(link):
    normalized = normalize_url(link)
    if not normalized:
        return ("", None, None)

    if "deezer" not in normalized:
        return (normalized, None, None)

    matchers = (
        ("track", r"/track/(.+)"),
        ("playlist", r"/playlist/(\d+)"),
        ("album", r"/album/(.+)"),
        ("artist_top", r"/artist/(\d+)/top_track"),
        ("artist_discography", r"/artist/(\d+)/discography"),
        ("artist", r"/artist/(\d+)"),
    )

    for link_type, pattern in matchers:
        match = re.search(pattern, normalized)
        if match:
            return (normalized, link_type, match.group(1))

    return (normalized, None, None)


def generateDownloadObject(dz, link, bitrate, plugins=None, listener=None):
    link, link_type, link_id = parseLink(link)

    if link_type is None or link_id is None:
        if plugins is None:
            plugins = {}
        for plugin in plugins.values():
            item = plugin.generateDownloadObject(dz, link, bitrate, listener)
            if item:
                return item
        raise LinkNotRecognized(link)

    if link_type == "track":
        return generateTrackItem(dz, link_id, bitrate)
    if link_type == "album":
        return generateAlbumItem(dz, link_id, bitrate)
    if link_type == "playlist":
        return generatePlaylistItem(dz, link_id, bitrate)
    if link_type == "artist":
        return generateArtistItem(dz, link_id, bitrate, listener)
    if link_type == "artist_discography":
        return generateArtistDiscographyItem(dz, link_id, bitrate, listener)
    if link_type == "artist_top":
        return generateArtistTopItem(dz, link_id, bitrate)

    raise LinkNotSupported(link)
