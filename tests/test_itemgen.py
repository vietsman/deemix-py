import copy

from deemix.itemgen import normalize_track_payload


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
