"""
use obspy to convert mseed to wav, then ffmpeg to conver wav to flac
"""

import os
import obspy
import glob

def mseed2wav(filenames):
    # resolve wildcard characters
    print(filenames)
    if type(filenames) == str:
        if '*' in filenames:
            filenames = glob.glob(filenames, recursive=True)
    else:
        if len(filenames) == 1:
            if '*' in filenames[0]:
                filenames = glob.glob(filenames[0], recursive=True)

    print(filenames)
    print('here')
    for filename in filenames:
        print(filename)
        if not filename.endswith('mseed'):
            continue
        print(filename)
        try:
            st = obspy.read(filename)
            wav_filename = filename.replace('mseed', 'wav')
            st.write(wav_filename, format='WAV')
            print(f"Converted {filename} to {wav_filename}")
            # Do NOT convert to flac or delete files
        except Exception as e:
            print(f'Failed to convert {filename}: {e}')
            continue

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filenames", nargs='+', type=str,
        help="Directory where mseed files are stored",
    )

    args = parser.parse_args()

    mseed2wav(args.filenames)