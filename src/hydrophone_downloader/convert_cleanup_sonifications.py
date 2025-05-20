#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import glob
from pydub import AudioSegment
from shutil import which
from tqdm import tqdm
from colorama import Fore, Style, init
import shutil
from collections import defaultdict
from datetime import datetime

# Dynamically determine the default sonifications directory
DEFAULT_SONIFICATIONS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "sonifications")
)
sonifications_dir = os.environ.get("SONIFICATIONS_DIR", DEFAULT_SONIFICATIONS_DIR)

init(autoreset=True)

def check_ffmpeg():
    """Check if ffmpeg is available."""
    if which("ffmpeg") is None:
        raise EnvironmentError("ffmpeg is not installed or not in PATH. Please install it for audio conversion.")

def wait_for_complete_deployment(folder, expected_count=288, poll_interval=30):
    """Wait until the folder contains the expected number of .flac files."""
    print(f"Waiting for {expected_count} .flac files in {folder} ...")
    while True:
        flac_files = glob.glob(os.path.join(folder, "*.flac"))
        if len(flac_files) >= expected_count:
            print(f"Detected {len(flac_files)} .flac files in {folder}.")
            return flac_files
        print(f"Currently {len(flac_files)} files. Waiting...")
        time.sleep(poll_interval)

def check_disk_space(folder):
    """Return free disk space in GB."""
    total, used, free = shutil.disk_usage(folder)
    free_gb = free / (1024 ** 3)
    return free_gb

def group_files_by_hydrophone(flac_files):
    """Group files by hydrophone name."""
    hydrophone_groups = defaultdict(list)
    for audio_file in flac_files:
        base = os.path.basename(audio_file)
        hydrophone_name = base.split("_")[0]
        hydrophone_groups[hydrophone_name].append(audio_file)
    return hydrophone_groups

def convert_and_merge_batches(hydrophone_groups, target_format, merged_dir, summary, station_folder):
    """Convert and merge .flac files in batches per hydrophone."""
    os.makedirs(merged_dir, exist_ok=True)
    for hydrophone_name, files in hydrophone_groups.items():
        files = sorted(files)
        batch_size = 12
        total_batches = (len(files) + batch_size - 1) // batch_size
        for batch_index in range(0, len(files), batch_size):
            batch_files = files[batch_index:batch_index + batch_size]
            if not batch_files:
                continue
            first_file = os.path.basename(batch_files[0])
            last_file = os.path.basename(batch_files[-1])
            try:
                first_timestamp = first_file.split("_")[1].split(".")[0]
                last_timestamp = last_file.split("_")[1].split(".")[0]
                start_date = datetime.strptime(first_timestamp[:8], "%Y%m%d").strftime("%Y%m%d")
                start_time = first_timestamp[9:15]
                end_time = last_timestamp[9:15]
            except (IndexError, ValueError) as e:
                print(f"{Fore.RED}Error extracting timestamps from filenames in batch: {hydrophone_name}")
                print(f"{Fore.RED}Error details: {e}")
                summary["errors"].append(f"Timestamp error in {hydrophone_name} batch: {e}")
                continue

            merged_filename = f"{hydrophone_name}_{start_date}T{start_time}_to_{end_time}.{target_format}"
            merged_filepath = os.path.join(merged_dir, merged_filename)

            if os.path.exists(merged_filepath):
                print(f"{Fore.LIGHTYELLOW_EX}Merged file already exists: {merged_filepath}. Skipping this batch.")
                continue

            merged_audio = AudioSegment.empty()
            valid_files = []
            for flac_file in tqdm(batch_files, desc=f"Merging batch for {hydrophone_name}", unit="file"):
                if os.path.getsize(flac_file) < 1024:
                    print(f"{Fore.YELLOW}File too small, skipping: {flac_file}")
                    summary["skipped"] += 1
                    try:
                        os.remove(flac_file)
                        summary["deleted"] += 1
                        print(f"{Fore.CYAN}Deleted small file: {flac_file}")
                    except Exception as e:
                        print(f"{Fore.RED}Error deleting small file: {flac_file}: {e}")
                        summary["errors"].append(f"{flac_file}: {e}")
                    continue
                try:
                    audio = AudioSegment.from_file(flac_file, format="flac")
                    merged_audio += audio
                    valid_files.append(flac_file)
                except Exception as e:
                    print(f"{Fore.RED}Error reading {flac_file}: {e}")
                    summary["errors"].append(f"{flac_file}: {e}")
                    summary["skipped"] += 1

            if not valid_files:
                continue

            free_space_gb = check_disk_space(merged_dir)
            if free_space_gb < 1:
                print(f"{Fore.RED}Insufficient disk space. Stopping conversion.")
                break

            try:
                if target_format == "wav":
                    merged_audio.export(merged_filepath, format="wav")
                else:
                    merged_audio.export(merged_filepath, format="mp3", bitrate="320k")
                print(f"{Fore.GREEN}Merged batch saved as: {merged_filepath}")
                summary["converted"] += 1

                # Only delete originals if merged file exists and is not empty
                if os.path.exists(merged_filepath) and os.path.getsize(merged_filepath) > 0:
                    for flac_file in valid_files:
                        try:
                            os.remove(flac_file)
                            summary["deleted"] += 1
                            print(f"{Fore.CYAN}Deleted original file: {flac_file}")
                        except Exception as e:
                            print(f"{Fore.RED}Error deleting file: {flac_file}: {e}")
                            summary["errors"].append(f"{flac_file}: {e}")
                else:
                    print(f"{Fore.RED}Merged file missing or empty, originals NOT deleted for batch: {merged_filepath}")
            except Exception as e:
                print(f"{Fore.RED}Error exporting merged batch for hydrophone {hydrophone_name}: {e}")
                summary["errors"].append(f"Export error for {merged_filepath}: {e}")

def main():
    check_ffmpeg()
    merged_dir = os.path.join(sonifications_dir, "merged")
    os.makedirs(merged_dir, exist_ok=True)

    print(f"Scanning sonifications_dir: {sonifications_dir}")

    total_summary = {
        "converted": 0,
        "deleted": 0,
        "skipped": 0,
        "errors": []
    }

    for folder_name in os.listdir(sonifications_dir):
        folder_path = os.path.join(sonifications_dir, folder_name)
        if not os.path.isdir(folder_path) or folder_name == "merged":
            continue

        flac_files_full = sorted(glob.glob(os.path.join(folder_path, "**", "*.flac"), recursive=True))
        print(f"Found {len(flac_files_full)} .flac files in {folder_path}")

        if not flac_files_full:
            print(f"{Fore.LIGHTYELLOW_EX}No .flac files found in folder: {folder_name}")
            continue

        summary = {
            "converted": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": []
        }

        while True:
            choice = input(f"Convert and merge files in '{folder_path}' to (wav/mp3/skip)? ").strip().lower()
            if choice in ("wav", "mp3"):
                if check_disk_space(merged_dir) < 1:
                    print(f"{Fore.RED}Insufficient disk space. Stopping conversion.")
                    break
                hydrophone_groups = group_files_by_hydrophone(flac_files_full)
                convert_and_merge_batches(hydrophone_groups, choice, merged_dir, summary, folder_name)
                print(f"{Fore.GREEN}All .flac files in {folder_path} converted, merged to {choice} in {merged_dir} and originals deleted.")
                break
            elif choice == "skip":
                print(f"{Fore.YELLOW}Skipping folder {folder_path}.")
                break
            else:
                print("Invalid choice. Please enter 'wav', 'mp3', or 'skip'.")

        # Remove temp folder if empty and it's a tmp_* folder
        if folder_name.startswith("tmp_") and not os.listdir(folder_path):
            try:
                os.rmdir(folder_path)
                print(f"{Fore.CYAN}Removed empty temporary folder: {folder_path}")
            except Exception as e:
                print(f"{Fore.RED}Could not remove folder {folder_path}: {e}")

        total_summary["converted"] += summary["converted"]
        total_summary["deleted"] += summary["deleted"]
        total_summary["skipped"] += summary["skipped"]
        total_summary["errors"].extend(summary["errors"])

    print("\nSummary of operations:")
    print(f"Total merged batches: {total_summary['converted']}")
    print(f"Total deleted: {total_summary['deleted']}")
    print(f"Total skipped (too small): {total_summary['skipped']}")
    if total_summary["errors"]:
        print(f"Errors encountered: {len(total_summary['errors'])}")
        for error in total_summary["errors"]:
            print(f" - {error}")
    print(f"{Fore.YELLOW}NOTE: Temporary folders (tmp_*) are managed by the script. Do not manually add files here.")

if __name__ == "__main__":
    main()