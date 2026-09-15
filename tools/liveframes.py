#!/usr/bin/env python3
"""Look at the MOTION in a Live Photo, not just the still Apple picked.

    python3 tools/liveframes.py p-6444          # contact sheet for one photograph
    python3 tools/liveframes.py p-6444 --fps 8  # denser sampling
    python3 tools/liveframes.py --list          # which originals have a live pair

WHY THIS EXISTS. p-6444 was captioned "asleep on a sandal". It is neither: the
object is a running shoe and the cat is ROLLING on it, rubbing his face along
it. Neither is knowable from the still, and I argued at some length that neither
was knowable at all -- until Ernie pointed out these are Live Photos. The .MOV
sits beside the .HEIC carrying a couple of seconds of video, and the roll is
unmistakable across ten frames.

94 of the 103 originals have one. Treating each original as a still and then
reasoning about the limits of stills was describing my own reading habit as a
property of the evidence. Before captioning an action, look at the pair.

WHAT IT CANNOT TELL YOU. Stillness in the pair is not evidence that nothing was
happening. Jasper stops whatever he is doing the moment he notices he is being
watched, and comes over for pets -- so the camera being ready is itself the thing
that ends the activity. p-9233 is exactly that: he had been playing with the
mouse, and the 2.5 seconds of video show a cat lying almost perfectly still,
because by then he had clocked the phone. Absence of motion here is evidence
about the photographer, not the cat.

mpv does the decoding. It is what Ernie uses, and the alternative found on this
machine was an ffmpeg bundled inside a fan-control application, which is not a
dependency anything should have.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genphotos

#  Portable builds under the profile; mpv is not on PATH here. Newest first.
MPV_CANDIDATES = [
    os.path.expanduser(r'~\mpv-20260829-x86_64-v3\mpv.exe'),
    os.path.expanduser(r'~\mpv-0.35.0-x86_64\mpv.exe'),
    'mpv',
]


def find_mpv():
    for c in MPV_CANDIDATES:
        if os.path.isfile(c):
            return c
        if os.sep not in c:
            from shutil import which
            p = which(c)
            if p:
                return p
    raise SystemExit('no mpv found; looked in %s' % ', '.join(MPV_CANDIDATES))


def live_pair(stem):
    """The .MOV beside the original for a given delivered stem, or None."""
    for row in genphotos.SOURCES:
        folder, fname, s = row[0], row[1], row[2]
        if s != stem:
            continue
        mov = os.path.join(genphotos.SRC_ROOT, folder, os.path.splitext(fname)[0] + '.MOV')
        return mov if os.path.exists(mov) else None
    raise SystemExit('no such stem in genphotos.SOURCES: %s' % stem)


def extract(mov, outdir, fps, width):
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith('.jpg'):
            os.remove(os.path.join(outdir, f))
    # --vo-image-format does NOT exist in mpv 0.41 and passing it makes the run
    # write nothing. Do not add --really-quiet: it hides that failure, and a
    # silenced error reading as "produced no frames" is how this was first
    # mistaken for mpv being unable to do the job at all.
    cmd = [find_mpv(), '--no-config', '--no-audio', '--vo=image',
           '--vo-image-outdir=' + outdir,
           '--vf=fps=%g,scale=%d:-2' % (fps, width), mov]
    r = subprocess.run(cmd, capture_output=True, text=True)
    frames = sorted(f for f in os.listdir(outdir) if f.endswith('.jpg'))
    if not frames:
        sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
        raise SystemExit('mpv wrote no frames; its output is above')
    return [os.path.join(outdir, f) for f in frames]


def contact_sheet(frames, path, cols=5):
    from PIL import Image
    ims = [Image.open(f) for f in frames]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * h), (10, 10, 14))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.thumbnail((1600, 1600), Image.LANCZOS)
    sheet.save(path)
    return sheet.size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('stem', nargs='?', help='delivered stem, e.g. p-6444')
    ap.add_argument('--fps', type=float, default=4.0)
    ap.add_argument('--width', type=int, default=480)
    ap.add_argument('--outdir', default=None)
    ap.add_argument('--list', action='store_true', help='which originals have a live pair')
    a = ap.parse_args()

    genphotos.require_repo_root()
    if a.list:
        have = [r[2] for r in genphotos.SOURCES if live_pair(r[2])]
        miss = [r[2] for r in genphotos.SOURCES if not live_pair(r[2])]
        print('live pair: %d of %d' % (len(have), len(have) + len(miss)))
        if miss:
            print('without one: %s' % ', '.join(miss))
        return

    if not a.stem:
        ap.error('give a stem, or --list')
    mov = live_pair(a.stem)
    if not mov:
        raise SystemExit('%s has no live pair' % a.stem)

    # .liveframes/ is gitignored. It has to be: this repo serves every path it
    # contains verbatim, so scratch frames committed here would be published.
    outdir = a.outdir or os.path.join('.liveframes', a.stem)
    frames = extract(mov, outdir, a.fps, a.width)
    # NAME THE SHEET AFTER THE SETTINGS THAT MADE IT. A fixed '_sheet.png' is
    # overwritten by the next run, so a second pass at a different fps silently
    # replaces the sheet someone was just told to open.
    sheet = os.path.join(outdir, '_sheet-fps%g-w%d.png' % (a.fps, a.width))
    size = contact_sheet(frames, sheet)
    print('%s: %d frames at %g fps -> %s (%dx%d)'
          % (a.stem, len(frames), a.fps, sheet, size[0], size[1]))


if __name__ == '__main__':
    main()
