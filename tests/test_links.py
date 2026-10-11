from deemix import parseLink


def test_parse_track_link_with_query_and_fragment():
    link, link_type, link_id = parseLink('https://www.deezer.com/track/12345?utm=1#frag')
    assert link == 'https://www.deezer.com/track/12345'
    assert link_type == 'track'
    assert link_id == '12345'


def test_parse_non_deezer_link_is_passthrough():
    link, link_type, link_id = parseLink('https://example.com/test')
    assert link == 'https://example.com/test'
    assert link_type is None
    assert link_id is None


def test_parse_invalid_input_returns_empty_tuple():
    link, link_type, link_id = parseLink(None)
    assert link == ''
    assert link_type is None
    assert link_id is None
