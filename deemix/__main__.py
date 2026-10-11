#!/usr/bin/env python3
from pathlib import Path
import logging
from typing import Iterable, List, Tuple

import click
from deezer import Deezer, TrackFormats

from deemix import generateDownloadObject
from deemix.contracts import DownloadFailure, DownloadRunResult
from deemix.downloader import Downloader
from deemix.itemgen import GenerationError
from deemix.settings import load as loadSettings
from deemix.utils import formatListener, getBitrateNumberFromText
import deemix.utils.localpaths as localpaths

try:
    from deemix.plugins.spotify import Spotify
except ImportError:
    Spotify = None


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_GENERATION = 4
EXIT_DOWNLOAD = 5

logger = logging.getLogger('deemix')


class LogListener:
    def __init__(self, *, quiet=False):
        self.quiet = quiet

    def send(self, key, value=None):
        if self.quiet:
            return
        log_string = formatListener(key, value)
        if log_string:
            click.echo(log_string)


def configure_logging(*, quiet: bool, verbose: int) -> None:
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


def resolve_config_folder(portable: bool) -> Path:
    return Path('.') / 'config' if portable else localpaths.getConfigFolder()


def request_valid_arl(dz: Deezer, prompt_fn=input) -> str:
    while True:
        arl = prompt_fn('Paste here your ARL:').strip()
        if dz.login_via_arl(arl):
            return arl
        click.echo('Invalid ARL. Please try again.', err=True)


def authenticate(dz: Deezer, config_folder: Path, prompt_fn=input) -> str:
    arl_file = config_folder / '.arl'
    arl_file.parent.mkdir(parents=True, exist_ok=True)

    arl = None
    if arl_file.is_file():
        lines = arl_file.read_text(encoding='utf-8').splitlines()
        arl = lines[0].strip() if lines else ''
        if not dz.login_via_arl(arl):
            arl = None

    if not arl:
        arl = request_valid_arl(dz, prompt_fn=prompt_fn)

    arl_file.write_text(arl, encoding='utf-8')
    return arl


def initialize_plugins(config_folder: Path):
    plugins = {}
    if Spotify:
        plugins['spotify'] = Spotify(configFolder=config_folder)
        plugins['spotify'].setup()
    return plugins


def resolve_bitrate(bitrate: str, settings: dict) -> int:
    if bitrate:
        return getBitrateNumberFromText(bitrate)
    return int(settings.get('maxBitrate', TrackFormats.MP3_320))


def expand_inputs(urls: Iterable[str]) -> List[str]:
    expanded: List[str] = []
    for entry in urls:
        if ';' in entry:
            parts = [part.strip() for part in entry.split(';') if part.strip()]
        else:
            parts = [entry.strip()]

        for part in parts:
            if not part:
                continue
            path = Path(part)
            if path.is_file():
                with open(path, encoding='utf-8') as file_handle:
                    for line in file_handle:
                        line = line.strip()
                        if line:
                            expanded.append(line)
            else:
                expanded.append(part)
    return expanded


def generate_download_objects(dz: Deezer, links: Iterable[str], bitrate: int, plugins: dict, listener: LogListener) -> Tuple[List[object], DownloadRunResult]:
    report = DownloadRunResult()
    objects = []
    for link in links:
        try:
            download_object = generateDownloadObject(dz, link, bitrate, plugins, listener)
        except GenerationError as error:
            report.generation_failures.append(DownloadFailure(stage='generation', message=error.message, link=error.link))
            click.echo(f'{error.link}: {error.message}', err=True)
            continue

        generated = download_object if isinstance(download_object, list) else [download_object]
        report.generated_items += len(generated)
        objects.extend(generated)

    return objects, report


def execute_queue(dz: Deezer, download_objects: Iterable[object], settings: dict, plugins: dict, listener: LogListener, report: DownloadRunResult) -> None:
    for obj in download_objects:
        current = obj
        try:
            if getattr(current, '__type__', None) == 'Convertable':
                plugin = plugins.get(current.plugin)
                if not plugin:
                    message = f"Plugin '{current.plugin}' is not available for conversion"
                    report.queue_failures.append(DownloadFailure(stage='conversion', message=message, item_id=str(current.id)))
                    click.echo(f'{current.type}:{current.id} - {message}', err=True)
                    continue
                current = plugin.convert(dz, current, settings, listener)
                report.converted_items += 1

            Downloader(dz, current, settings, listener).start()
            report.completed_items += 1
            if getattr(current, 'failed', 0):
                report.queue_failures.append(
                    DownloadFailure(
                        stage='download',
                        message=f"{current.failed} track(s) failed",
                        item_id=str(current.id),
                    )
                )
        except Exception as exc:
            report.queue_failures.append(
                DownloadFailure(
                    stage='queue',
                    message=str(exc),
                    item_id=str(getattr(current, 'id', 'unknown')),
                )
            )
            logger.exception('Queue execution error for %s', getattr(current, 'id', 'unknown'))
            click.echo(f"{getattr(current, 'type', 'item')}:{getattr(current, 'id', 'unknown')} - {exc}", err=True)


def summarize_results(report: DownloadRunResult, download_objects: Iterable[object]) -> int:
    source_count = 0
    accepted_count = 0
    skipped_count = 0
    failed_track_count = 0

    for obj in download_objects:
        source_count += int(getattr(obj, 'sourceSize', getattr(obj, 'size', 0)) or 0)
        accepted_count += int(getattr(obj, 'acceptedSize', getattr(obj, 'size', 0)) or 0)
        skipped_count += len(getattr(obj, 'skipped', []) or [])
        failed_track_count += int(getattr(obj, 'failed', 0) or 0)

    click.echo(
        'Summary: '
        f'items={report.generated_items}, '
        f'completed={report.completed_items}, '
        f'source_tracks={source_count}, '
        f'accepted_tracks={accepted_count}, '
        f'skipped_tracks={skipped_count}, '
        f'failed_tracks={failed_track_count}'
    )

    if report.generation_failures:
        return EXIT_GENERATION
    if report.queue_failures or failed_track_count:
        return EXIT_DOWNLOAD
    return EXIT_OK


def apply_cli_overrides(settings: dict, path: str):
    if path is None:
        return settings
    if path == '':
        path = '.'
    settings['downloadLocation'] = str(Path(path))
    return settings


@click.command()
@click.option('--portable', is_flag=True, help='Create the config folder in the current directory.')
@click.option('-b', '--bitrate', default=None, help='Override the configured bitrate.')
@click.option('-p', '--path', type=str, help='Download destination folder.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress normal progress output.')
@click.option('-v', '--verbose', count=True, help='Increase log verbosity (-v, -vv).')
@click.argument('url', nargs=-1, required=True)
def download(url, bitrate, portable, path, quiet, verbose):
    """Download links using deemix URL [URL ...]."""
    try:
        configure_logging(quiet=quiet, verbose=verbose)

        config_folder = resolve_config_folder(portable)
        settings = apply_cli_overrides(loadSettings(config_folder), path)
        listener = LogListener(quiet=quiet)
        dz = Deezer()

        try:
            authenticate(dz, config_folder)
        except KeyboardInterrupt:
            click.echo('Authentication canceled by user.', err=True)
            raise SystemExit(EXIT_AUTH)

        plugins = initialize_plugins(config_folder)

        links = expand_inputs(url)
        if not links:
            click.echo('No valid URLs were provided.', err=True)
            raise SystemExit(EXIT_USAGE)

        resolved_bitrate = resolve_bitrate(bitrate, settings)
        objects, report = generate_download_objects(dz, links, resolved_bitrate, plugins, listener)
        if not objects and report.generation_failures:
            raise SystemExit(summarize_results(report, objects))

        execute_queue(dz, objects, settings, plugins, listener, report)
        raise SystemExit(summarize_results(report, objects))
    except SystemExit:
        raise
    except Exception as exc:
        click.echo(f'Error: {exc}', err=True)
        raise SystemExit(EXIT_DOWNLOAD)


if __name__ == '__main__':
    download()  # pylint: disable=E1120
