from pathlib import Path

from click.testing import CliRunner

import deemix.__main__ as cli
from deemix.contracts import DownloadRunResult


class FakeObject:
    __type__ = 'Collection'

    def __init__(self, item_id='1'):
        self.id = item_id
        self.type = 'playlist'
        self.failed = 0
        self.size = 1
        self.sourceSize = 1
        self.acceptedSize = 1
        self.skipped = []


class FakeDeezer:
    pass


def test_expand_inputs_from_file_and_delimited_values(tmp_path):
    links_file = tmp_path / 'links.txt'
    links_file.write_text('https://deezer.com/track/1\n\nhttps://deezer.com/track/2\n', encoding='utf-8')

    links = cli.expand_inputs((f'https://deezer.com/track/3;https://deezer.com/track/4', str(links_file)))
    assert links == [
        'https://deezer.com/track/3',
        'https://deezer.com/track/4',
        'https://deezer.com/track/1',
        'https://deezer.com/track/2',
    ]


def test_download_command_runs_with_mocked_pipeline(monkeypatch):
    monkeypatch.setattr(cli, 'configure_logging', lambda **_: None)
    monkeypatch.setattr(cli, 'loadSettings', lambda *_: {'maxBitrate': '3', 'downloadLocation': '.'})
    monkeypatch.setattr(cli, 'Deezer', FakeDeezer)
    monkeypatch.setattr(cli, 'authenticate', lambda *_args, **_kwargs: 'arl')
    monkeypatch.setattr(cli, 'initialize_plugins', lambda *_: {})

    def fake_generate(*_args, **_kwargs):
        report = DownloadRunResult(generated_items=1)
        return [FakeObject()], report

    monkeypatch.setattr(cli, 'generate_download_objects', fake_generate)
    monkeypatch.setattr(cli, 'execute_queue', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, 'summarize_results', lambda *_args, **_kwargs: 0)

    runner = CliRunner()
    result = runner.invoke(cli.download, ['https://deezer.com/track/1'])
    assert result.exit_code == 0


def test_execute_queue_isolates_item_failures(monkeypatch):
    report = DownloadRunResult(generated_items=2)
    seen = []

    class FakeDownloader:
        def __init__(self, _dz, obj, _settings, _listener):
            self.obj = obj

        def start(self):
            seen.append(self.obj.id)
            if self.obj.id == '1':
                self.obj.failed = 1
            if self.obj.id == '2':
                raise RuntimeError('boom')

    monkeypatch.setattr(cli, 'Downloader', FakeDownloader)

    obj1 = FakeObject('1')
    obj2 = FakeObject('2')

    cli.execute_queue(FakeDeezer(), [obj1, obj2], {}, {}, cli.LogListener(quiet=True), report)

    assert seen == ['1', '2']
    assert len(report.queue_failures) == 2
    assert report.queue_failures[0].stage == 'download'
    assert report.queue_failures[1].stage == 'queue'
