import os
import subprocess


def convert720p(source):
    base_name, _ = os.path.splitext(source)

    new_file = f"{base_name}_720p.mp4"

    cmd = 'ffmpeg -i "{}" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(
        source, new_file
    )
    run = subprocess.run(cmd, capture_output=True, shell=True)
    return run