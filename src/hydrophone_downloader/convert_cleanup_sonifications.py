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

# Set your sonifications directory here (portable version)
sonifications_dir = os.environ.get(
    "SONIFICATIONS_DIR",
    os.path.join(os.path.expanduser("~"), "sonifications")
)

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

def convert_files(flac_files, target_format, merged_dir, summary):
    """Convert .flac files to .wav or .mp3 (320kbps) in merged_dir and delete originals."""
    os.makedirs(merged_dir, exist_ok=True)
    for flac_file in tqdm(flac_files, desc=f"Converting files", unit="file"):
        if os.path.getsize(flac_file) < 1024:  # Skip files smaller than 1KB
            print(f"{Fore.YELLOW}File too small, skipping: {flac_file}")
            summary["skipped"] += 1
            continue
        base = os.path.splitext(os.path.basename(flac_file))[0]
        if target_format == "wav":
            out_file = os.path.join(merged_dir, base + ".wav")
        elif target_format == "mp3":
            out_file = os.path.join(merged_dir, base + ".mp3")
        else:
            print(f"{Fore.RED}Unknown format: {target_format}{Style.RESET_ALL}")
            summary["errors"].append(f"Unknown format for {flac_file}")
            continue
        try:
            audio = AudioSegment.from_file(flac_file, format="flac")
            if target_format == "wav":
                audio.export(out_file, format="wav")
            else:
                audio.export(out_file, format="mp3", bitrate="320k")
            print(f"{Fore.GREEN}Converted {flac_file} -> {out_file}")
            os.remove(flac_file)
            print(f"{Fore.CYAN}Deleted {flac_file}")
            summary["converted"] += 1
            summary["deleted"] += 1
        except Exception as e:
            print(f"{Fore.RED}Error converting {flac_file}: {e}{Style.RESET_ALL}")
            summary["errors"].append(f"{flac_file}: {e}")

def check_disk_space(folder):
    """Return free disk space in GB."""
    total, used, free = shutil.disk_usage(folder)
    free_gb = free / (1024 ** 3)
    return free_gb

def main():
    check_ffmpeg()
    merged_dir = os.path.join(sonifications_dir, "merged")
    os.makedirs(merged_dir, exist_ok=True)

    # List all deployment folders in sonifications, skip 'merged' itself
    deployment_folders = [
        os.path.join(sonifications_dir, d)
        for d in os.listdir(sonifications_dir)
        if os.path.isdir(os.path.join(sonifications_dir, d)) and d != "merged"
    ]

    summary = {
        "converted": 0,
        "deleted": 0,
        "skipped": 0,
        "errors": []
    }

    for folder in deployment_folders:
        flac_files = glob.glob(os.path.join(folder, "*.flac"))
        if not flac_files:
            continue

        # Wait for all files to be downloaded
        flac_files = wait_for_complete_deployment(folder)

        # Ask user for conversion format
        while True:
            choice = input(f"Convert files in '{folder}' to (wav/mp3/skip)? ").strip().lower()
            if choice in ("wav", "mp3"):
                if check_disk_space(merged_dir) < 1:  # Less than 1GB free
                    print(f"{Fore.RED}Insufficient disk space. Stopping conversion.")
                    break
                convert_files(flac_files, choice, merged_dir, summary)
                print(f"{Fore.GREEN}All .flac files in {folder} converted to {choice} in {merged_dir} and originals deleted.")
                break
            elif choice == "skip":
                print(f"{Fore.YELLOW}Skipping folder {folder}.")
                break
            else:
                print("Invalid choice. Please enter 'wav', 'mp3', or 'skip'.")

    # Print summary
    print("\nSummary of operations:")
    print(f"Total converted: {summary['converted']}")
    print(f"Total deleted: {summary['deleted']}")
    print(f"Total skipped (too small): {summary['skipped']}")
    if summary["errors"]:
        print(f"Errors encountered: {len(summary['errors'])}")
        for error in summary["errors"]:
            print(f" - {error}")

if __name__ == "__main__":
    main()
