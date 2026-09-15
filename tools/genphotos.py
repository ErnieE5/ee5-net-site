#!/usr/bin/env python3
"""Build the site's photographs from the iPhone originals.

THE ORIGINALS ARE NEVER WRITTEN. Everything under d:\\iPhone is opened read-only
and stays exactly as it was; this script only ever writes into photos/.

Both a WebP and a JPEG are produced for every picture, and BOTH ARE BUILT FROM
THE ORIGINAL. Transcoding the delivered JPEG into WebP instead would stack a
second lossy pass on top of the first, and the artefacts of the first pass are
exactly the high-frequency noise the second one spends its bits preserving.

REDACTIONS AND TONE ARE DATA, listed beside the file they belong to. They were
one-off commands once, which meant a rebuild would silently have published an
unblurred plate: the safety of the output depended on somebody remembering. It
no longer does.
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

#  The desk in the two office-chair pictures. Statements with a legible credit
#  union letterhead, addressed envelopes, and a letter with readable body text.
DESK_A_L = (0, 470, 960, 1270, 26, 12)     # 0059: the mail pile, left
DESK_A_R = (2280, 680, 3024, 1180, 26, 12) # 0059: the statement under the towel roll
DESK_B_L = (0, 480, 820, 1060, 24, 11)     # 9543: paperwork, left
DESK_B_M = (1590, 420, 2390, 820, 24, 11)  # 9543: the letter beside the keyboard
DESK_B_BIN = (0, 1360, 360, 1810, 22, 10)  # 9543: papers in the bin

#  The driveway shot. The plate is the obvious one; the SUBDIVISION MONUMENT
#  across the street is the one that nearly got through, and it names the
#  development, which is the same class of fact as the door number already
#  blurred in p-4532. A photograph of a house does not have to show its number
#  to say where it is.
DRIVE_PLATE = (3270, 1920, 3348, 2092, 13, 7)
DRIVE_SIGN  = (3462, 1210, 3668, 1318, 15, 8)
DRIVE_SIGN2 = (3788, 1276, 3978, 1358, 14, 7)

#  A blemish, not a redaction: nothing here is being hidden from anyone, it is
#  just a mark he would rather not have on the front page. (x0,y0,x1,y1,feather).
NOSE = [(926, 1592, 974, 1630, 6), (898, 1616, 958, 1648, 6)]

#  file, stem, redactions, tone, heals
#  `tone` is a shadow-lift gamma: >1 brightens shadows and midtones and leaves
#  highlights where they are.
SOURCES = [
    ('202609_a', 'IMG_0667.HEIC', 'p-0667', [], None),
    ('202609_a', 'IMG_0677.HEIC', 'p-0677', [], None),
    ('202608_a', 'IMG_0645.HEIC', 'p-0645', [], None),
    ('202606_a', 'IMG_0511.HEIC', 'p-0511', [], None),
    ('202606_a', 'IMG_0527.HEIC', 'p-0527', [], None),
    ('202605_a', 'EQOZ6328.JPG',  'p-6328', [TAG], None),
    ('202605_a', 'LYQG4532.JPG',  'p-4532', [PLATE, NUMBER], None),
    ('202604_a', 'IMG_0270.HEIC', 'p-0270', [], None),
    ('202604_a', 'IMG_0287.HEIC', 'p-0287', [], None),
    ('202603_a', 'IMG_0184.HEIC', 'p-0184', [], None),
    ('202603_a', 'IMG_0191.HEIC', 'p-0191', [], None),
    ('202602_a', 'DOHM3038.JPG',  'p-3038', [], None),
    ('202602_a', 'IMG_0008.HEIC', 'p-0008', [], None),
    ('202602_a', 'IMG_0053.HEIC', 'p-0053', [], None),
    ('202602_a', 'IMG_0123.HEIC', 'p-0123', [], None),
    ('202602_a', 'IMG_0139.HEIC', 'p-0139', [], None),
    ('202602_a', 'IMG_0059.HEIC', 'p-0059', [DESK_A_L, DESK_A_R], None),
    ('202601_a', 'IMG_9334.HEIC', 'p-9334', [], None),
    ('202601_a', 'IMG_9383.HEIC', 'p-9383', [], None),
    # Garnet is backlit by a bright window and reads as a silhouette. The lift is
    # global on purpose: it is strongest in the shadows, which IS the cat, and
    # weakest in the highlights, which is the blown window behind. A rectangle
    # brightened around the cat would have pulled the window up with it and left
    # a visible bright patch.
    ('202601_a', 'IMG_9529.HEIC', 'p-9529', [], 1.34),
    ('202601_a', 'IMG_9543.HEIC', 'p-9543', [DESK_B_L, DESK_B_M, DESK_B_BIN], None),
    ('202601_a', 'IMG_9548.HEIC', 'p-9548', [], None),
    ('202601_a', 'IMG_9555.HEIC', 'p-9555', [], None),
    ('202601_a', 'IMG_9572.HEIC', 'p-9572', [], None),
    ('202601_a', 'IMG_9576.HEIC', 'p-9576', [], None),
    ('202601_a', 'IMG_9583.HEIC', 'p-9583', [], None),
    ('202601_a', 'IMG_E9326.HEIC', 'p-9326', [], None),
    ('202601_a', 'JAOW5768.JPG',  'p-5768', [], None),
    ('202601_a', 'LRSQ8701.JPG',  'p-8701', [], None),
    ('202512_a', 'HHDY8933.JPG',  'p-8933', [], None),
    ('202512_a', 'IMG_8986.HEIC', 'p-8986', [], None),
    ('202512_a', 'IMG_9016.HEIC', 'p-9016', [], None),
    ('202512_a', 'IMG_9078.HEIC', 'p-9078', [], None),
    ('202512_a', 'IMG_9106.HEIC', 'p-9106', [], None),
    ('202512_a', 'IMG_9169.HEIC', 'p-9169', [], None),
    ('202512_a', 'IMG_9233.HEIC', 'p-9233', [], None),
    ('202512_a', 'IMG_9246.HEIC', 'p-9246', [], None),
    ('202512_a', 'IMG_9269.HEIC', 'p-9269', [], None),
    ('202511_a', 'IMG_8909.HEIC', 'p-8909', [], None),
    # Stage light is hard shadow and saturated colour; a small lift opens the
    # faces without touching the neon, which is already at the top of the range.
    ('202510_a', 'IMG_8497.HEIC', 'p-8497', [], 1.12),
    ('202510_a', 'IMG_8533.HEIC', 'p-8533', [], None, NOSE),
    ('202510_a', 'IMG_8548.HEIC', 'p-8548', [], None),
    ('202510_a', 'IMG_8571.HEIC', 'p-8571', [], None),
    ('202510_a', 'IMG_8581.HEIC', 'p-8581', [], None),
    ('202510_a', 'IMG_8584.HEIC', 'p-8584', [], None),
    ('202510_a', 'IMG_8589.HEIC', 'p-8589', [], None),
    ('202510_a', 'IMG_8591.HEIC', 'p-8591', [], None),
    ('202510_a', 'IMG_8593.HEIC', 'p-8593', [], None),
    ('202510_a', 'IMG_8601.HEIC', 'p-8601', [], None),
    ('202510_a', 'IMG_8627.HEIC', 'p-8627', [], None),
    ('202509_a', 'IMG_8353.HEIC', 'p-8353', [], None),
    # Night stage, so a small lift opens the players without touching the lamps.
    ('202508_a', 'IMG_8233.HEIC', 'p-8233', [], 1.15),
    ('202508_a', 'IMG_8291.HEIC', 'p-8291', [], None),
    ('202507_a', 'IMG_8083.HEIC', 'p-8083', [DRIVE_PLATE, DRIVE_SIGN, DRIVE_SIGN2], None),
    ('202507_a', 'IMG_8086.HEIC', 'p-8086', [], None),
    ('202507_a', 'IMG_8142.HEIC', 'p-8142', [], None),
    ('202507_a', 'IMG_8158.HEIC', 'p-8158', [], None),
    ('202507_a', 'IMG_8168.HEIC', 'p-8168', [], None),
    ('202506_a', 'IMG_8060.HEIC', 'p-8060', [], None),
    ('202506_a', 'IMG_8074.HEIC', 'p-8074', [], None),
    ('202410_a', 'IMG_6727.HEIC', 'p-6727', [], None),
    ('202409_a', 'IMG_6680.HEIC', 'p-6680', [], None),
    ('202408_a', 'IMG_6512.HEIC', 'p-6512', [], 1.18),
    ('202408_a', 'IMG_6529.HEIC', 'p-6529', [], None),
    ('202408_a', 'IMG_6566.HEIC', 'p-6566', [], 1.20),
    ('202407_a', 'IMG_6322.HEIC', 'p-6322', [], None),
    ('202407_a', 'IMG_6411.HEIC', 'p-6411', [], None),
    ('202407_a', 'IMG_6444.HEIC', 'p-6444', [], None),
    ('202406_a', 'IMG_6132.HEIC', 'p-6132', [], None),
    ('202406_a', 'IMG_6154.HEIC', 'p-6154', [], None),
    ('202406_a', 'IMG_6195.HEIC', 'p-6195', [], None),
    ('202406_a', 'IMG_6198.HEIC', 'p-6198', [], None),
    ('202406_a', 'IMG_6202.HEIC', 'p-6202', [], None),
    ('202406_a', 'IMG_6207.HEIC', 'p-6207', [], None),
    ('202406_a', 'IMG_6300.HEIC', 'p-6300', [], 1.12),
]


def soft_blur(im, box):
    """Blur a region and feather it back in.

    A hard-edged rectangle reads as a censor bar and draws the eye straight to
    what was hidden. A feathered mask reads as depth of field. Softness is the
    disguise; the RADIUS is the mechanism, and it has to be large enough that the
    glyphs are gone rather than merely soft.

    THE WORKING CROP IS CLAMPED TO THE IMAGE. Pillow fills an out-of-bounds crop
    with black, so a region touching an edge -- and the desk piles run off the
    left edge -- would have had that black blurred inward and pasted back as a
    dark band along the border.
    """
    x0, y0, x1, y1, radius, feather = box
    pad = feather * 3
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    reg = im.crop((cx0, cy0, cx1, cy1))
    blur = reg.filter(ImageFilter.GaussianBlur(radius))
    mask = Image.new('L', reg.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (x0 - cx0, y0 - cy0, x1 - cx0 - 1, y1 - cy0 - 1),
        radius=max(4, min(x1 - x0, y1 - y0) // 3), fill=255)
    reg.paste(blur, (0, 0), mask.filter(ImageFilter.GaussianBlur(feather)))
    im.paste(reg, (cx0, cy0))
    return im


def inpaint(im, spec, iters=26, pad=26):
    """Fill a small region with an interpolation of the skin around it.

    NOT a clone stamp. There is no good donor patch for a blemish on a face lit
    from one side: any skin lifted from beside it arrives at the wrong brightness
    and lands as a visible rectangle, which is more conspicuous than the mark it
    replaced. Tried that first; it looked worse.

    The hole is filled from its own boundary instead. Each pass blurs the current
    state and keeps that result only INSIDE the hole, restoring everything outside
    it, so colour creeps inward from the rim a little further every pass until the
    hole holds a smooth continuation of its surroundings. Cheap, and exactly right
    for a small mark on an otherwise even surface.
    """
    x0, y0, x1, y1, feather = spec
    cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
    cx1, cy1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
    reg = im.crop((cx0, cy0, cx1, cy1))
    hole = Image.new('L', reg.size, 0)
    ImageDraw.Draw(hole).ellipse((x0 - cx0, y0 - cy0, x1 - cx0 - 1, y1 - cy0 - 1), fill=255)
    cur = reg.copy()
    for _ in range(iters):
        cur = Image.composite(cur.filter(ImageFilter.GaussianBlur(5)), reg, hole)
    reg.paste(cur, (0, 0), hole.filter(ImageFilter.GaussianBlur(feather)))
    im.paste(reg, (cx0, cy0))
    return im

def shadow_lift(im, gamma):
    """Brighten shadows and midtones, leaving highlights alone.

    A gamma curve is the right shape for "the subject is too dark because it is
    backlit": it moves 64 a long way, 128 less, and 250 barely at all, so a dark
    subject comes up while a blown window stays where it is. Pure white is a
    fixed point, so nothing can be pushed past it and clip.
    """
    lut = [round(255.0 * ((v / 255.0) ** (1.0 / gamma))) for v in range(256)]
    return im.point(lut * len(im.getbands()))


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
    for row in SOURCES:
        folder, fname, stem, redactions, tone = row[:5]
        heals = row[5] if len(row) > 5 else []
        src = os.path.join(SRC_ROOT, folder, fname)
        if not os.path.exists(src):
            raise SystemExit('missing original: %s' % src)

        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        for box in redactions:
            im = soft_blur(im, box)
        for spec in heals:
            im = inpaint(im, spec)
        if tone:
            im = shadow_lift(im, tone)

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
        note = []
        if redactions:
            note.append('%d redacted' % len(redactions))
        if heals:
            note.append('%d healed' % len(heals))
        if tone:
            note.append('tone %.2f' % tone)
        print('%-8s %4dx%-4d  jpg %6.1f KB   webp %6.1f KB   %+5.1f%%%s'
              % (stem, im.width, im.height, j / 1024, w / 1024,
                 (w - j) / j * 100, ('   [' + ', '.join(note) + ']') if note else ''))

    tj = sum(r[2] for r in rows)
    tw = sum(r[3] for r in rows)
    print('-' * 74)
    print('%-8s %-10s  jpg %6.1f KB   webp %6.1f KB   %+5.1f%%   (%d pictures)'
          % ('total', '', tj / 1024, tw / 1024, (tw - tj) / tj * 100, len(rows)))
    return rows


if __name__ == '__main__':
    build()
