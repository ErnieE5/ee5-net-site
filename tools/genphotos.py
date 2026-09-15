#!/usr/bin/env python3
"""Build the site's photographs from the iPhone originals.

THE ORIGINALS ARE NEVER WRITTEN. Everything under d:\\iPhone is opened read-only
and stays exactly as it was; this script only ever writes into photos/.

Both a WebP and a JPEG are produced for every picture, and BOTH ARE BUILT FROM
THE ORIGINAL. Transcoding the delivered JPEG into WebP instead would stack a
second lossy pass on top of the first, and the artefacts of the first pass are
exactly the high-frequency noise the second one spends its bits preserving.

REDACTIONS ARE DATA, listed beside the file they belong to. They were one-off
commands before, which meant a rebuild would silently have published an unblurred
plate: the safety of the output depended on somebody remembering. Now it does not.
"""
import os
from PIL import Image, ImageOps, ImageFilter, ImageDraw

SRC_ROOT = r'D:\iPhone'
OUT = 'photos'
LONG = 1600
JPEG_Q = 82
WEBP_Q = 80

#  (x0, y0, x1, y1, blur radius, feather) in the ORIGINAL's pixel coordinates,
#  after EXIF rotation is applied.
PLATE  = (368, 1450, 446, 1494, 14, 7)     # Texas plate, front of the CR-V
NUMBER = (1286, 1258, 1330, 1342, 16, 8)   # door number, stacked on the garage pillar
TAG    = (2548, 1986, 2806, 2172, 22, 9)   # handwritten luggage tag: names and a number

SOURCES = [
    ('202609_a', 'IMG_0667.HEIC', 'p-0667', []),
    ('202609_a', 'IMG_0677.HEIC', 'p-0677', []),
    ('202608_a', 'IMG_0645.HEIC', 'p-0645', []),
    ('202606_a', 'IMG_0511.HEIC', 'p-0511', []),
    ('202606_a', 'IMG_0527.HEIC', 'p-0527', []),
    ('202605_a', 'EQOZ6328.JPG',  'p-6328', [TAG]),
    ('202605_a', 'LYQG4532.JPG',  'p-4532', [PLATE, NUMBER]),
    ('202604_a', 'IMG_0270.HEIC', 'p-0270', []),
    ('202604_a', 'IMG_0287.HEIC', 'p-0287', []),
    ('202603_a', 'IMG_0184.HEIC', 'p-0184', []),
    ('202603_a', 'IMG_0191.HEIC', 'p-0191', []),
    ('202602_a', 'DOHM3038.JPG',  'p-3038', []),
    ('202602_a', 'IMG_0008.HEIC', 'p-0008', []),
    ('202602_a', 'IMG_0053.HEIC', 'p-0053', []),
    ('202602_a', 'IMG_0123.HEIC', 'p-0123', []),
    ('202602_a', 'IMG_0139.HEIC', 'p-0139', []),
]


def soft_blur(im, box):
    """Blur a region and feather it back in.

    A hard-edged rectangle reads as a censor bar and draws the eye straight to
    what was hidden. A feathered mask reads as depth of field. Softness is the
    disguise; the RADIUS is the mechanism, and it has to be large enough that the
    glyphs are gone rather than merely soft.
    """
    x0, y0, x1, y1, radius, feather = box
    pad = feather * 3
    reg = im.crop((x0 - pad, y0 - pad, x1 + pad, y1 + pad))
    blur = reg.filter(ImageFilter.GaussianBlur(radius))
    mask = Image.new('L', reg.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (pad, pad, reg.width - pad - 1, reg.height - pad - 1),
        radius=max(4, min(x1 - x0, y1 - y0) // 3), fill=255)
    reg.paste(blur, (0, 0), mask.filter(ImageFilter.GaussianBlur(feather)))
    im.paste(reg, (x0 - pad, y0 - pad))
    return im



def require_repo_root():
    """Refuse to run anywhere but the site root.

    Both scripts address photos/ and index.html relatively. Run from the wrong
    directory they do not fail -- they quietly build a photos/ folder somewhere
    else, or rewrite an index.html that is not the site's, and report success
    doing it. A wrong answer delivered confidently is the failure worth guarding.
    """
    import sys
    if not (os.path.isfile('CNAME') and os.path.isfile('index.html')):
        sys.exit('run this from the ee5-net-site root (CNAME and index.html must be here); cwd is %s'
                 % os.getcwd())

def build():
    require_repo_root()
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        raise SystemExit('pillow_heif is required to read the HEIC originals')

    os.makedirs(OUT, exist_ok=True)
    rows = []
    for folder, fname, stem, redactions in SOURCES:
        src = os.path.join(SRC_ROOT, folder, fname)
        if not os.path.exists(src):
            raise SystemExit('missing original: %s' % src)

        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        for box in redactions:
            im = soft_blur(im, box)

        # Colour, not identity: iPhones shoot Display P3, and dropping the profile
        # shifts every hue. Kept; everything else in .info is discarded, because
        # Pillow re-emits whatever it finds there -- EXIF, XMP, Photoshop blocks --
        # and getexif() reporting zero tags does NOT mean the file is clean.
        icc = im.info.get('icc_profile')
        im.info = {}
        im.thumbnail((LONG, LONG), Image.LANCZOS)

        jpg = os.path.join(OUT, stem + '.jpg')
        web = os.path.join(OUT, stem + '.webp')
        im.save(jpg, 'JPEG', quality=JPEG_Q, optimize=True, progressive=True, icc_profile=icc)
        im.save(web, 'WEBP', quality=WEBP_Q, method=6, icc_profile=icc)

        j, w = os.path.getsize(jpg), os.path.getsize(web)
        rows.append((stem, im.size, j, w, len(redactions)))
        print('%-8s %4dx%-4d  jpg %6.1f KB   webp %6.1f KB   %+5.1f%%%s'
              % (stem, im.width, im.height, j / 1024, w / 1024,
                 (w - j) / j * 100, '   [redacted]' if redactions else ''))

    tj = sum(r[2] for r in rows)
    tw = sum(r[3] for r in rows)
    print('-' * 68)
    print('%-8s %-10s  jpg %6.1f KB   webp %6.1f KB   %+5.1f%%'
          % ('total', '', tj / 1024, tw / 1024, (tw - tj) / tj * 100))
    return rows


if __name__ == '__main__':
    build()
