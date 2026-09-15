# tools

The build pipeline for ee5.net. There is no build step for the *site* — committing
to `main` publishes it — but the photographs and the rail markup are generated, and
these are the generators. Run both from the repo root; they refuse to run anywhere
else rather than quietly writing into the wrong directory.

```bash
python3 tools/genphotos.py          # d:\iPhone originals  ->  photos/*.jpg + *.webp
python3 tools/genrail.py index.html # photos/  ->  the <ul> between the RAIL markers
```

## genphotos.py

Builds every delivered picture from its iPhone original. **Nothing under `d:\iPhone`
is ever written.**

Both a WebP and a JPEG come out, and **both are built from the original** — transcoding
the delivered JPEG into WebP would stack a second lossy pass on the first, and the
artefacts of the first pass are exactly the high-frequency detail the second one then
spends its bits preserving.

**The redactions are data**, in `PLATE`, `NUMBER` and `TAG`, listed against the file
they belong to in `SOURCES`. This is the point of the script existing: they were
one-off commands once, which meant a rebuild would have quietly republished an
unblurred plate, with the safety of the output depending on somebody remembering.
If you add a picture that needs something hidden, add the box here — not in a
throwaway command.

Two metadata traps, both learned the hard way:

- `getexif()` reporting zero tags does **not** mean the file is clean. Pillow re-emits
  whatever it finds in `info` — EXIF, XMP, Photoshop blocks — so `im.info = {}` is
  required. A 2432-byte XMP segment survived a save that looked spotless.
- The ICC profile must be kept. iPhones shoot Display P3, and dropping it shifts
  every hue.

## genrail.py

Rewrites the block between the `RAIL-BEGIN` / `RAIL-END` markers in `index.html`, and
re-inserts `rail.css` and the wave script. Everything about a picture is one row of
`PHOTOS`: its file, its frame style, a short label, and its alt text. Adding a
photograph is adding a row.

**One frame style per picture, never both** — `clips` keeps the straight edge and hangs
four gold metal corners on it; `wave` cuts the edge into a sine and hangs nothing. A
frame is a decision about an edge, and two decisions about one edge is an argument.

The comment above `PHOTOS` carries the caption rules and the facts Ernie has supplied
about what is actually in the pictures. Read it before writing a caption; it exists
because those facts were twice lost and twice re-derived.

## liveframes.py

Most of these originals are **Live Photos**: a `.MOV` sits beside the `.HEIC`
with a couple of seconds of video in it. 94 of 103 have one.

```bash
python3 tools/liveframes.py --list      # which originals have a pair
python3 tools/liveframes.py p-6444      # contact sheet of the motion
```

This exists because `p-6444` was captioned "asleep on a sandal" and is neither:
it is a running shoe and the cat is rolling on it. I argued the motion was
unknowable from a photograph before Ernie pointed out that the photograph is not
all there is. **Before captioning an action, look at the pair.**

It drives `mpv`, which is not on PATH here — the portable builds are under the
profile and the script knows where. `--vo-image-format` does not exist in mpv
0.41 and passing it writes nothing at all, so the script does not pass it and
does not pass `--really-quiet` either: a silenced failure looks exactly like
"produced no frames".

Frames land in `.liveframes/`, which is gitignored and must stay that way —
`.nojekyll` means anything committed here is published.

## rail.css

Spliced into `index.html` by `genrail.py`. Edit it here, never in `index.html` — the
next run overwrites the copy there.
