import json

from deemix.settings import DEFAULTS, check, load, save


def test_load_recovers_from_invalid_json(tmp_path):
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / 'config.json').write_text('{not-json}', encoding='utf-8')

    settings = load(config_dir)
    assert settings['downloadLocation'] == DEFAULTS['downloadLocation']


def test_load_normalizes_missing_templates_and_tags(tmp_path):
    config_dir = tmp_path / 'config'
    save({'downloadLocation': '/tmp/downloads', 'tags': {'title': False}}, config_dir)

    settings = load(config_dir)
    assert settings['downloadLocation'] == '/tmp/downloads'
    assert settings['tracknameTemplate'] == DEFAULTS['tracknameTemplate']
    assert settings['tags']['title'] is False
    assert 'artist' in settings['tags']


def test_check_detects_non_normalized_settings():
    assert check({'tags': {'title': False}}) == 1
    assert check(DEFAULTS) == 0
