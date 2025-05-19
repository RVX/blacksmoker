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

### What does this command do?

This command downloads hydrophone data for a specific region, depth, and time range, and saves it to the `sonifications` folder in your project directory.

#### Parameter Breakdown:

- `min_latitude` / `max_latitude`:  
  The latitude range (in degrees) for the area you want to search.

- `min_longitude` / `max_longitude`:  
  The longitude range (in degrees) for the area you want to search.

- `min_depth` / `max_depth`:  
  The depth range (in meters) for the data you want (e.g., from the surface to 4000 meters deep).

- `start_time` / `end_time`:  
  The date range for the data you want, in `YYYY-MM-DD` format.

- `save_dir`:  
  The folder where downloaded data will be saved.  
  Using `./sonifications` means the data will be stored in a folder named `sonifications` in your current directory.

#### Example in Plain English

> Download all hydrophone data collected between January 1 and January 3, 2025,  
> from latitudes 45 to 50, longitudes -131 to -129, and depths 0 to 4000 meters,  
> and save the results in the `sonifications` folder.

### How the Program Works

When you run the command:

```sh
hydrophone-downloader min_latitude=45 max_latitude=50 min_longitude=-131 max_longitude=-129 min_depth=0 max_depth=4000 start_time="2025-01-01" end_time="2025-01-03" save_dir="./sonifications"
```

the following scripts and modules are involved:

- **`src/hydrophone_downloader/cli.py`**  
  This is the main entry point. It parses your command-line arguments and loads configuration, then calls the main download logic.

- **`src/hydrophone_downloader/downloader.py`**  
  This script contains the `download_data` function, which coordinates the download process for all supported data sources (ONC, OOI, etc.).

- **`src/hydrophone_downloader/supported_classes/onc_class.py`**  
  Handles downloading and organizing data from Ocean Networks Canada (ONC).

- **`src/hydrophone_downloader/supported_classes/ooi_class.py`**  
  Handles downloading and organizing data from the Ocean Observatories Initiative (OOI).

- **`src/hydrophone_downloader/merge_station_wav_files.py`**  
  (Optional, run separately) Used to merge and batch audio files after downloading, if needed.

- **`src/hydrophone_downloader/convert_cleanup_sonifications.py or merge_station_wav_files.py`**  
  (Optional, run separately) Used to convert and clean up downloaded audio files.

**How it works:**  
1. The CLI (`cli.py`) receives your parameters and calls `download_data` in `downloader.py`.
2. `downloader.py` determines which data sources to use and calls the appropriate class (`onc_class.py` for ONC, `ooi_class.py` for OOI).
3. Each class downloads data into the `sonifications` folder (or your chosen `save_dir`).
4. After download, you can use the merge and conversion scripts to further process your data.


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


