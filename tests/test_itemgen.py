import copy

from deemix.itemgen import generatePlaylistItem, normalize_track_payload


def test_empty_media_is_skipped():
    payload = {"MEDIA": [], "SNG_ID": 123, "SNG_TITLE": "Broken Track"}
    assert normalize_track_payload(payload, context="playlist", position=4) is None


def test_non_dict_payload_is_skipped():
    assert normalize_track_payload([], context="album", position=1) is None


def test_valid_payload_is_mapped():
    payload = {
        "SNG_ID": 42,
        "SNG_TITLE": "Example Track",
        "ART_NAME": "Example Artist",
        "ALB_TITLE": "Example Album",
        "MEDIA": [{"HREF": "https://example.invalid/preview.mp3"}],
        "DURATION": 180,
        "EXPLICIT_LYRICS": 0,
        "TRACK_TOKEN": "token",
        "TRACK_TOKEN_EXPIRE": 123,
        "MEDIA_VERSION": "v1",
        "FILESIZE": 321,
        "FALLBACK_ID": "0",
    }

    mapped = normalize_track_payload(payload, context="track", position=7)
    assert mapped is not None
    assert mapped["id"] == 42
    assert mapped["title"] == "Example Track"
    assert mapped["artist"]["name"] == "Example Artist"


def test_playlist_collection_accounting_and_skip_positions():
    class FakeDZ:
        class api:
            @staticmethod
            def get_artist(_artist_id):
                return {'id': 5080, 'name': 'Various Artists'}

    valid_track = {
        "SNG_ID": 101,
        "SNG_TITLE": "Track One",
        "ART_NAME": "Artist",
        "ALB_TITLE": "Album",
        "MEDIA": [{"HREF": "https://example.invalid/preview1.mp3"}],
        "DURATION": 100,
        "EXPLICIT_LYRICS": 0,
        "TRACK_TOKEN": "token1",
        "TRACK_TOKEN_EXPIRE": 123,
        "MEDIA_VERSION": "v1",
        "FILESIZE": 111,
        "FALLBACK_ID": "0",
    }
    second_valid_track = copy.deepcopy(valid_track)
    second_valid_track["SNG_ID"] = 202
    second_valid_track["SNG_TITLE"] = "Track Three"
    second_valid_track["MEDIA"] = [{"HREF": "https://example.invalid/preview3.mp3"}]

    malformed_track = {"SNG_ID": 303, "SNG_TITLE": "Broken", "MEDIA": []}
    playlist_tracks = [valid_track, malformed_track, second_valid_track]

    playlist_api = {
        "title": "Example Playlist",
        "creator": {"name": "Tester", "id": "1"},
        "picture_small": "https://e-cdns-images.dzcdn.net/images/playlist/test/56x56-000000-80-0-0.jpg",
        "public": True,
    }

    item = generatePlaylistItem(
        FakeDZ(),
        "1",
        3,
        playlistAPI=playlist_api,
        playlistTracksAPI=playlist_tracks,
    )

    assert item.sourceSize == 3
    assert item.acceptedSize == 2
    assert item.size == 2
    assert len(item.skipped) == 1
    assert item.skipped[0]["position"] == 2
    assert [track["position"] for track in item.collection["tracks"]] == [1, 3]
    assert "TRACK_TOKEN" in valid_track
