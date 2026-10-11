# ![](./icon.svg) deemix

deemix is a Deezer downloader library with a CLI entrypoint.

## Installation

### From PyPI

```bash
python3 -m pip install deemix
```

Then run:

```bash
deemix --help
```

### From source

```bash
git clone https://github.com/vietsman/deemix-py.git
cd deemix-py
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

## CLI usage

Primary invocation remains:

```bash
deemix URL [URL ...]
```

Examples:

```bash
deemix https://www.deezer.com/track/3135556
deemix "https://www.deezer.com/track/1;https://www.deezer.com/track/2"
deemix /path/to/links.txt
```

Useful options:

- `--portable` create `./config` in the current working directory
- `-b, --bitrate` override configured bitrate
- `-p, --path` override download destination
- `-q, --quiet` suppress progress logs
- `-v/-vv, --verbose` increase logging verbosity

## Configuration

Settings are stored in `config.json` under the deemix config folder (or `./config` with `--portable`).
Authentication uses `.arl` in the same config folder.

Public compatibility APIs remain available:

- `deemix.parseLink`
- `deemix.generateDownloadObject`
- `deemix.settings.load`
- `deemix.settings.save`
- `deemix.settings.check`

## Error handling and malformed tracks

The downloader now treats malformed Deezer payloads as skipped items instead of hard failures.
This includes tracks with empty `MEDIA` arrays or invalid payload shapes.

For playlist/album-like collections, deemix tracks:

- source item count
- accepted item count
- skipped item count
- failed download count

A malformed track should not abort an entire collection.

## Development

### Run tests

```bash
pytest
```

Tests are mock/offline oriented and must not contact Deezer APIs.

## License

This project is licensed under GPLv3. See `LICENSE.txt`.
