# hydrophone_downloader

A Python package for downloading, converting, and merging hydrophone data from various sources.
Original code Bret Nestor --> https://github.com/bnestor/hydrophone_downloader
Mods by RVX in 2025

## Features

- Download hydrophone data from ONC, OOI, and more
- Convert between mseed, flac, wav, and mp3
- Merge and clean up audio files

## Installation

Requirements: Python 3.8+

```sh
pip install git+https://github.com/RVX/blacksmoker.git
```

Or for development:

```sh
git clone https://github.com/RVX/blacksmoker.git
cd blacksmoker
pip install -e .
```

## Usage

Example command:

```sh
hydrophone-downloader min_latitude=45 max_latitude=50 min_longitude=-131 max_longitude=-129 min_depth=0 max_depth=4000 start_time="2025-01-01" end_time="2025-01-03" save_dir="./sonifications"
```


Run the CLI:

```sh
python -m hydrophone_downloader.cli
```

### Customizing Data Paths

You can specify where your data is stored and where merged files are written using command-line options:

```sh
python src/hydrophone_downloader/merge_station_wav_files.py --base-dir /path/to/sonifications --output-dir /path/to/merged
```

- `--base-dir` sets the directory containing your temporary audio folders (default: `sonifications/` relative to the project).
- `--output-dir` sets the directory for merged files (default: `sonifications/merged/`).

These options work on any operating system.  
**Tip:** Use forward slashes `/` or double backslashes `\\` on Windows, or just use the default relative paths.

## Configuration

Edit the config files in `src/hydrophone_downloader/configs/` as needed.

## License

MIT License (see LICENSE file)

