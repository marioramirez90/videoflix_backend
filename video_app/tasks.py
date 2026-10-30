import os
import subprocess


def convert720p(source):
    """
    Diese Funktion wird vom Hintergrund-Worker ausgeführt,
    ohne dass das Frontend oder das Backend blockieren.
    """
    base_name, _ = os.path.splitext(source)

    new_file = f"{base_name}_720p.mp4"

    cmd = 'ffmpeg -i "{}" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(
        source, new_file
    )

    print(f"[WORKER] Starte Konvertierung im Hintergrund: {new_file}")

    run = subprocess.run(cmd, capture_output=True, shell=True)

    print(f"[WORKER] Konvertierung beendet: {new_file}")
    return run