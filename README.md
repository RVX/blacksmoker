# hydrophone_downloader

A Python package for downloading, converting, and merging hydrophone data from various sources.

## Features

- Download hydrophone data from ONC, OOI, and more
- Convert between mseed, flac, wav, and mp3
- Merge and clean up audio files

## Installation

Requirements: Python 3.8+

```sh
pip install git+https://github.com/yourusername/hydrophone_downloader.git
```

Or for development:

```sh
git clone https://github.com/yourusername/hydrophone_downloader.git
cd hydrophone_downloader
pip install -e .
```

## Usage

Run the CLI:

```sh
python -m hydrophone_downloader.cli
```

## Configuration

Edit the config files in `src/hydrophone_downloader/configs/` as needed.

## License

MIT License (see LICENSE file)

