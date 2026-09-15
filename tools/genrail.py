#!/usr/bin/env python3
"""Replace the fixed easel wall with a scrollable rail of photographs.

THE PHOTOGRAPHS ARE A LIST.  Everything about a picture lives in one row of
PHOTOS below: its file, which frame style it wears, and what it shows.  Adding a
picture is adding a row; reordering them is reordering rows.  Nothing else in
the page knows how many there are.
"""
import re, sys, os
from PIL import Image

#  WHAT IS IN THESE PICTURES, and how each claim is known. Read this before
#  writing a caption; it exists because most of it was got wrong once first.
#
#  THE CATS. Garnet has the white bib and white paws; Jasper has neither. Every
#  attribution here was made from the markings in the frame, not from the order
#  the files arrived. Both are male ("the boys"), so pronouns are available.
#
#  ALT TEXT DESCRIBES WHAT IS IN THE FRAME, and only that. A description that
#  states more than the picture shows is wrong in the one place nobody sighted
#  will catch it, because the people relying on it cannot check it against the
#  image. Four mistakes of one kind were made here before that sank in:
#
#    a cabinet got a KITCHEN       - which turned out to be true, see below
#    the cat tree got a WALL       - the dark timber filling p-0645 IS the tree,
#                                    and the blue in its gaps is the mural behind
#    the shelving got MAPLE        - a species guessed from a colour
#    a stateroom got a LOUNGE      - p-8701, because the art is big and the
#                                    lighting built in
#
#  The move is always the same: the photograph shows a SURFACE or a FITTING, and
#  the place or substance it belongs to is a separate claim. Describe the finish
#  and the fitting; leave the room and the material to whoever owns them.
#
#  BUT A FACT HE SUPPLIES IS NOT AN INFERENCE. "kitchen cabinet" was scrubbed for
#  being unverifiable and it was simply true. The caution is against ASSERTING
#  what cannot be seen, never against keeping what the owner has said. His facts
#  are recorded here so a later pass cannot tidy them away again:
#
#    - the white cabinets are the kitchen's, running along two walls
#    - the cat tree is the piece against the blue-and-gold mural, AND it is
#      wall-mounted and wider than that mural, so its outer perches stand against
#      plain wall. The mural is sufficient evidence of the tree, never necessary:
#      p-9555 was called a "wall shelf" on that error and p-9246 shows the whole
#      S-curve running past the mural's edge
#    - the floor that looks like planks is VINYL, wood-adjacent rather than wood
#    - the pale shelving is an old, durable IKEA set and even he is not sure of
#      the wood, which is the whole argument for saying "pale wood" and stopping
#    - the house in p-4532 is his own
#    - Jasper is on his LEG in p-9548, not his arm
#    - the 2024 frames show Jasper in a PINK COLLAR with a tag; the 2025 ones show
#      neither cat collared. That is an observation, not something he has said, so
#      it dates a photograph loosely and identifies nobody. The muzzle still does
#      the identifying: Garnet's is white and shows even in profile.
#    - OUINESS IS AN ENSEMBLE with different members each time, so it is credited
#      as a band and nobody in it is named. LINE OF FIRE has been T.J. Wade and
#      Anne for as long as he has known them, which is why naming those two is
#      safe and stays consistent across every frame they appear in.
#
#  THE PLACES are named with his leave to name them and be corrected. How each
#  one is known, because the confidence is not uniform:
#
#    READ FROM THE FRAME   Ensenada (the sign is in it), San Diego (the USS
#                          Midway at the pier, the twin Hyatt towers)
#    OWN GPS               Cabo 0.6 km, Ensenada 0.6 km, San Juan 0.7 km,
#                          St Thomas 1.3 km, Cozumel, Antigua, Lake Charles
#    BRACKETED             an edited export loses its GPS but keeps its clock,
#                          and the frames either side of it kept both. Roatan
#                          sits between 16.313,-86.544 and 16.270,-86.575; the
#                          deck shot between two Cozumel readings 98 minutes
#                          each way and 290 m apart, which is one berth and a
#                          day alongside
#
#  AND THE HAT IS NOT EVIDENCE. Roatan's caption once leaned partly on the ROATAN
#  hat; that hat is on his head at COZUMEL in p-9169. A souvenir travels, so it
#  locates nothing. Coordinates carry that caption now.
#  A HOUSE DOES NOT HAVE TO SHOW ITS NUMBER TO SAY WHERE IT IS. p-8083 looks out
#  across the street at the SUBDIVISION MONUMENT, which names the development.
#  That is the same class of fact as the door number already blurred in p-4532,
#  and it nearly went out because the check had been "find the number and the
#  plate" rather than "find what locates this house". Both are blurred now, with
#  two smaller signs beside it. p-4532 itself was re-swept and carries no signage.
#
#  PRECISION HAS A LIMIT TOO. The four Dominican frames sit between Taino Bay and
#  Amber Cove, the two Puerto Plata cruise ports, about 500 m from one and 1.3 km
#  from the other. That is not enough to pick one, so the caption names the city
#  and stops. A coordinate is not automatically a fine-grained answer.
#
#
#  BRACKETING HAS A LIMIT, and p-8533 is past it: no GPS, and its nearest
#  geotagged neighbour is 8.7 HOURS earlier on a day running Austin, Houston,
#  Lake Charles. Two readings an hour either side of a moored ship pin it; one
#  reading half a day earlier during a drive pins nothing. Last known position is
#  not evidence, so that caption names no place.
#
#        file            style    label              alt text
PHOTOS = [
    ('p-0667.jpg', 'clips', 'Garnet',
     'Garnet, a tabby cat with a white bib and white paws, sitting upright on top of a carpeted scratching post.'),
    ('p-0677.jpg', 'wave',  'Jasper & Garnet',
     'Jasper and Garnet lying side by side on top of the kitchen cabinets, peering over the edge.'),
    ('p-0645.jpg', 'clips', 'Garnet & Jasper',
     'Garnet looking out from an upper nook of the cat tree, with Jasper settled in another below.'),
    ('p-0511.jpg', 'wave',  'Garnet',
     'Garnet loafing on a bright blue shag rug and looking at the camera.'),
    ('p-0527.jpg', 'clips', 'Jasper',
     'Jasper curled up asleep in a flat Red Bull box on a pale wood-look floor.'),
    ('p-6328.jpg', 'wave',  'Jasper & Garnet',
     'Jasper on a pale wood shelving unit with Garnet on the shelf below, beside black soft-sided pet carriers.'),
    ('p-0270.jpg', 'clips', 'Jasper & Garnet',
     'Jasper stretched along a platform of the cat tree, with Garnet tucked into the fleece-lined nook below.'),
    ('p-0287.jpg', 'wave',  'Jasper & Garnet',
     'Jasper sitting on a step of the cat tree looking up, with Garnet asleep in a fleece bed behind.'),
    ('p-0184.jpg', 'clips', 'Jasper & Ernie',
     "Jasper asleep on Ernie's chest, the pair of them horizontal beside a bright window."),
    ('p-0191.jpg', 'wave',  'Jasper',
     "Jasper curled asleep in one of the cat tree's fleece cradles, one paw hooked over the edge."),
    ('p-3038.jpg', 'clips', 'St Thomas',
     'The Norwegian Viva at her berth in Charlotte Amalie, St Thomas, seen from the hillside above the harbour.'),
    ('p-0008.jpg', 'wave',  'Cozumel',
     "The bow of the Norwegian Viva at the pier in Cozumel, the Celebrity Silhouette moored alongside."),
    ('p-0053.jpg', 'clips', 'Garnet',
     'Garnet sprawled on the blue shag rug, cheek resting in a cupped hand.'),
    ('p-0123.jpg', 'wave',  'Garnet & Jasper',
     'Garnet and Jasper standing over the wreckage of a paper towel roll on the blue rug.'),
    ('p-0139.jpg', 'clips', 'Garnet & Jasper',
     'Garnet looking down from an upper platform of the cat tree, with Jasper in the fleece cradle below.'),
    ("p-0059.jpg", "clips", "Garnet & Jasper",
     "Garnet and Jasper sharing the office chair, Jasper looking over Garnet's shoulder."),
    ("p-9543.jpg", "wave",  "Jasper & Garnet",
     "Jasper mid-yawn in the office chair, with Garnet dozing beside him."),
    ("p-9529.jpg", "clips", "Garnet",
     "Garnet perched on top of a sisal scratching post, backlit by the window behind him."),
    ("p-9576.jpg", "wave",  "Garnet",
     "Garnet standing on top of the sisal post, tail stretched out behind him."),
    ("p-9548.jpg", "clips", "Jasper",
     "Jasper asleep with his head resting on Ernie's leg, close up."),
    ("p-9555.jpg", "wave",  "Jasper & Garnet",
     "Jasper mid-yawn on one perch of the cat tree, while Garnet lies in the fleece hammock beside him."),
    ("p-9572.jpg", "clips", "Jasper & Garnet",
     "Jasper standing over Garnet, who is sprawled on a striped runner along the media console."),
    ("p-9334.jpg", "wave",  "Ensenada",
     "The cruise ship Norwegian Jade behind the big ENSENADA letters, palms in front."),
    ('p-9383.jpg', 'clips', 'Cabo San Lucas',
     "El Arco and the sea stacks at Land's End, Cabo San Lucas, a small boat passing at sunset."),
    ('p-9326.jpg', 'wave', 'leaving San Diego',
     "The San Diego skyline receding behind the ship's wake, the USS Midway at the pier."),
    ("p-9583.jpg", "clips", "Ernie",
     "Ernie in a straw hat stamped ROATAN, sitting by a curved window."),
    ("p-9246.jpg", "clips", "the cat tree",
     "The whole cat tree: Jasper on a lower perch and Garnet on an upper one, against the blue mural."),
    ("p-9106.jpg", "wave",  "Garnet & Jasper",
     "Garnet in a fleece nook of the cat tree, with Jasper stretched out on the perch above."),
    ("p-8933.jpg", "clips", "Garnet & Jasper",
     "Garnet and Jasper curled up together in the cat tree's fleece hammock."),
    ("p-9269.jpg", "wave",  "Garnet & Jasper",
     "Garnet and Jasper stacked in the office chair again, Jasper propped up behind Garnet."),
    ("p-9233.jpg", "clips", "he got a mouse",
     "Jasper on the blue rug with a computer mouse pinned under one paw."),
    ("p-9078.jpg", "wave",  "towel animal",
     "A towel animal perched on the arm of a sofa, holding the TV remote."),
    ("p-9016.jpg", "clips", "rubber duck",
     "A giant rubber duck riding in the bridge wing of a cruise ship."),
    ('p-5768.jpg', 'wave', 'San Juan',
     'Four cruise ships in San Juan harbour, seen from the fort wall above Old San Juan.'),
    ('p-8986.jpg', 'clips', 'Ernie',
     'Ernie in the ROATAN hat on a balcony above the painted rooftops of Roatán.'),
    ("p-9169.jpg", "wave",  "Ernie",
     "Ernie in the ROATAN hat and sunglasses, out on deck at Cozumel."),
    ("p-8701.jpg", "clips", "Ernie",
     "Ernie in an orange shirt in his stateroom at Antigua, a large abstract painting behind him."),
    ("p-8497.jpg", "wave",  "Line of Fire",
     "T.J. Wade on keys and Anne on drums, the band Line of Fire playing an Austin bar under a carnival mural and a giant pink elephant."),
    ("p-8909.jpg", "clips", "Ernie",
     "Ernie in a hotel in Lake Charles, Louisiana, a barber shop and a tiled column behind him."),
    ("p-8533.jpg", "wave",  "Ernie",
     "Ernie in a black cowboy hat with a patterned band, city lights through the window behind him."),
    ("p-8548.jpg", "clips", "Jasper",
     "Jasper stretched to full height up the window glass, watching a squirrel in a window feeder."),
    ("p-8291.jpg", "wave",  "a squirrel",
     "A squirrel sprawled flat on the patio in the heat, all four legs stretched straight out."),
    ("p-8233.jpg", "clips", "Line of Fire",
     "T.J. Wade on keys and Anne on drums, Line of Fire playing an outdoor stage in Austin at night."),
    ("p-8571.jpg", "wave",  "leaving Miami",
     "The Miami shoreline astern as the ship leaves port."),
    ("p-8581.jpg", "clips", "at sea",
     "Sunset over the ship's wake in open water."),
    ("p-8584.jpg", "wave",  "Puerto Plata",
     "The bow of the Norwegian Aqua alongside at Puerto Plata, Dominican Republic."),
    ("p-8589.jpg", "clips", "Puerto Plata",
     "The painted hull of the Norwegian Aqua at Puerto Plata, a crane and a freighter beyond."),
    ("p-8591.jpg", "wave",  "Puerto Plata",
     "The Norwegian Aqua in full profile at Puerto Plata, seen across the rocks."),
    ("p-8593.jpg", "clips", "Puerto Plata",
     "The Norwegian Aqua seen over a hedge from the beach at Puerto Plata."),
    ("p-8601.jpg", "wave",  "St Thomas",
     "Charlotte Amalie from the hillside, the Norwegian Aqua and a Costa ship at the piers."),
    ("p-8627.jpg", "clips", "Tortola",
     "Leaving Road Town, Tortola under a heavy sky, the pier falling astern."),
    ("p-8353.jpg", "wave",  "Ernie",
     "Ernie on deck at Galveston, the ship's glass canopy behind him."),
    ("p-8158.jpg", "wave",  "who me",
     "Jasper sitting innocently on the paper towel roll he has just unrolled across the rug."),
    ("p-8168.jpg", "clips", "Jasper & Garnet",
     "Jasper and Garnet both up on their hind legs at the window, reaching towards the feeder."),
    ("p-8086.jpg", "wave",  "Jasper & Garnet",
     "Jasper stretched up the window with Garnet sitting beside him, both watching the feeder."),
    ("p-8142.jpg", "clips", "a squirrel",
     "A squirrel clinging to the wall to raid a lantern-shaped bird feeder over the fence."),
    ("p-8060.jpg", "wave",  "Ouiness",
     "The band Ouiness playing under a carport, seven of them, with stuffed animals watching from child-sized chairs."),
    ("p-8074.jpg", "clips", "Line of Fire",
     "Anne on drums and T.J. Wade on keys, Line of Fire playing outdoors in the evening."),
    ("p-6727.jpg", "wave",  "Garnet",
     "Garnet dozing on top of the fridge with one white paw over the edge, below the kitchen cabinets."),
    ("p-6680.jpg", "clips", "Line of Fire",
     "T.J. Wade on keys in a light-up jacket and Anne on drums, Line of Fire under a liquid light show."),
    ("p-6529.jpg", "wave",  "Jasper",
     "Jasper sitting among the groceries on a pantry shelf, wearing a pink collar."),
    ("p-6512.jpg", "clips", "Jasper",
     "Jasper perched on the kitchen counter, peering down into an opened cabinet at the pull-out hamper."),
    ("p-6566.jpg", "wave",  "Jasper",
     "Jasper looking down from the top of the fridge, in the gap above the kitchen cabinets."),
    # Not a beast. Published only with the door number and the plate blurred out.
    ('p-4532.jpg', 'wave',  'home',
     "Ernie's house, seen from the street on a clear day, with a blue SUV parked in the driveway."),
    ("p-8083.jpg", "wave",  "home",
     "The blue SUV on the driveway at Ernie's house, the porch and garage behind it."),
]

SHUFFLE = """    <script>
    /*  THE HANG IS RESHUFFLED ON EVERY LOAD.

        This runs INLINE, immediately after the list it reorders, and that
        placement is the whole trick: parsing stops at a synchronous script, so
        the reordering happens before the browser has painted anything.  The same
        code at the end of <body> would show the authored order first and visibly
        snap into a new one.

        Fisher-Yates, walking down and swapping with a random earlier index --
        every permutation equally likely.  Sorting by `Math.random() - 0.5`
        instead is the usual shortcut and it is biased, because a comparator that
        answers differently each time it is asked about the same pair is not an
        ordering and the sort's result depends on its algorithm.

        `loading` is then re-decided FROM THE NEW ORDER.  It was authored as eager
        for the first three, but after a shuffle those three are somewhere else,
        and a lazily-loaded picture in the leftmost frame arrives late in the one
        position where it is certain to be looked at. */
    (function () {
      var rail = document.currentScript.previousElementSibling;
      if (!rail || rail.tagName !== 'UL') return;
      var items = [].slice.call(rail.children), i, j;
      for (i = items.length - 1; i > 0; i--) {
        j = Math.floor(Math.random() * (i + 1));
        if (i !== j) { var t = items[i]; items[i] = items[j]; items[j] = t; }
      }
      var frag = document.createDocumentFragment();
      items.forEach(function (li, n) {
        var img = li.querySelector('img');
        if (img) img.loading = n < 3 ? 'eager' : 'lazy';
        frag.appendChild(li);
      });
      rail.appendChild(frag);
    })();
    </script>"""

CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rail.css')

JS = r'''
/*  THE WAVE FRAME ON THE PHOTOGRAPHS.

    Only `.shot.wave` needs a script at all: the `clips` style is four rotated
    background images and is done entirely in CSS.  Here the picture is clipped
    to a sine silhouette and the same path is stroked over it, twice -- a dark
    line under a light one, which is easel's answer to an edge that would
    otherwise disappear into whatever it is standing on.

    The path is rebuilt from the rendered size rather than scaled, so period and
    amplitude stay constant however tall the rail is drawn: the point of
    `docs/nine-slice-or-geometry.md`, where no band of the silhouette repeats. */
(function () {
  'use strict';
  var PERIOD = 150, AMP = 9, STROKE = 2;
  var SVGNS = 'http://www.w3.org/2000/svg';

  function sineRect(w, h) {
    var inset = AMP + STROKE, d = [], started = false;
    var bw = w - 2 * inset, bh = h - 2 * inset;
    if (bw < 4 * AMP || bh < 4 * AMP) return '';
    function edge(len, fn) {
      var n = Math.max(1, Math.round(len / PERIOD)), half = len / (2 * n), k, s, c, e;
      if (!started) { var p = fn(0, 0); d.push('M' + p[0].toFixed(1) + ' ' + p[1].toFixed(1)); started = true; }
      for (k = 0; k < 2 * n; k++) {
        s = (k % 2 === 0) ? 2 * AMP : -2 * AMP;
        c = fn((k + 0.5) * half, s);
        e = fn((k + 1) * half, 0);
        d.push('Q' + c[0].toFixed(1) + ' ' + c[1].toFixed(1) + ' ' + e[0].toFixed(1) + ' ' + e[1].toFixed(1));
      }
    }
    edge(bw, function (t, o) { return [inset + t, inset - o]; });
    edge(bh, function (t, o) { return [inset + bw + o, inset + t]; });
    edge(bw, function (t, o) { return [inset + bw - t, inset + bh + o]; });
    edge(bh, function (t, o) { return [inset - o, inset + bh - t]; });
    return d.join(' ') + ' Z';
  }

  function draw(shot) {
    var img = shot.querySelector('img');
    if (!img) return;
    var w = img.offsetWidth, h = img.offsetHeight;
    // A frame built from a zero measurement is an outline drawn around nothing.
    // The markup carries width/height so this should not happen, but a stylesheet
    // that has not applied yet can still report zero, so it is checked anyway.
    if (!w || !h) return;
    var dd = sineRect(w, h);
    if (!dd) return;
    img.style.clipPath = 'path("' + dd + '")';
    var svg = shot.querySelector('svg.edgepath');
    if (!svg) {
      svg = document.createElementNS(SVGNS, 'svg');
      svg.setAttribute('class', 'edgepath');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      ['under', 'over'].forEach(function (cls) {
        var p = document.createElementNS(SVGNS, 'path');
        p.setAttribute('class', cls);
        svg.appendChild(p);
      });
      shot.appendChild(svg);
    }
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    svg.setAttribute('width', w);
    svg.setAttribute('height', h);
    [].forEach.call(svg.querySelectorAll('path'), function (p) { p.setAttribute('d', dd); });
  }

  var waves = [].slice.call(document.querySelectorAll('.shot.wave'));
  waves.forEach(function (shot) {
    var img = shot.querySelector('img');
    draw(shot);
    if (img && !img.complete) img.addEventListener('load', function () { draw(shot); });
  });

  if (window.ResizeObserver) {
    var ro = new ResizeObserver(function (es) { es.forEach(function (e) { draw(e.target); }); });
    waves.forEach(function (s) { ro.observe(s); });
  } else {
    var t;
    window.addEventListener('resize', function () {
      clearTimeout(t); t = setTimeout(function () { waves.forEach(draw); }, 120);
    });
  }

  /*  A horizontal scroller is invisible to a wheel that only sends deltaY, which
      is most of them. Translating vertical wheel to horizontal makes the rail work
      with an ordinary mouse; the guard hands the gesture back to the page once the
      rail is against either end, so the page never feels stuck. */
  var rail = document.querySelector('.rail');
  if (rail) {
    rail.addEventListener('wheel', function (ev) {
      if (ev.deltaY === 0 || Math.abs(ev.deltaX) > Math.abs(ev.deltaY)) return;
      var atStart = rail.scrollLeft <= 0 && ev.deltaY < 0;
      var atEnd = rail.scrollLeft >= rail.scrollWidth - rail.clientWidth - 1 && ev.deltaY > 0;
      if (atStart || atEnd) return;
      ev.preventDefault();
      rail.scrollLeft += ev.deltaY;
    }, { passive: false });
  }
})();
'''


def dimensions(path):
    """Real pixel size, read from the file rather than assumed."""
    with Image.open(path) as im:
        return im.size


def markup():
    out = ['  <div class="railwrap">',
           '    <ul class="rail" tabindex="0" role="region" aria-label="Photographs">']
    for i, (f, style, _label, alt) in enumerate(PHOTOS):
        w, h = dimensions('photos/' + f)
        # WIDTH AND HEIGHT ARE NOT OPTIONAL HERE. A lazily-loaded image has no
        # intrinsic size until it arrives, so the frame script measured zero and
        # drew a wave around nothing. Declaring the real pixel size lets the
        # browser reserve the box up front, so the frame is right before the
        # bytes land and the rail does not reflow as they do.
        #
        # WEBP FIRST, JPEG BEHIND IT. Both are built from the iPhone original by
        # genphotos.py, so neither is a transcode of the other and neither carries
        # the other's artefacts. The <img> keeps the JPEG, so it stays the element
        # every script and stylesheet here already talks to, and anything that
        # cannot read WebP still gets a picture.
        out.append('      <li class="shot %s">' % style)
        out.append('        <picture>')
        out.append('          <source srcset="photos/%s" type="image/webp">' % (f[:-4] + '.webp'))
        out.append('          <img src="photos/%s" alt="%s"' % (f, alt))
        out.append('               width="%d" height="%d" loading="%s" decoding="async">'
                   % (w, h, 'eager' if i < 3 else 'lazy'))
        out.append('        </picture>')
        # THE CAPTION IS THE ALT TEXT, SHOWN. It is marked aria-hidden because the
        # <img> beside it already carries the identical sentence in `alt`: without
        # that, a screen reader meets the same description twice in a row. A `title`
        # attribute would have the same fault, and is slow to appear and cannot be
        # styled, so this is a real element instead.
        out.append('        <span class="cap-t" aria-hidden="true">%s</span>' % alt)
        if style == 'clips':
            out.append('        <span class="cl ul"></span><span class="cl ur"></span>'
                       '<span class="cl lr"></span><span class="cl ll"></span>')
        out.append('      </li>')
    out += ['    </ul>', SHUFFLE, '  </div>']
    return '\n'.join(out)



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

def main():
    """Guarded, because IMPORTING this module used to rewrite index.html.

    The splice ran at module level, so `import genrail` -- to read the PHOTOS
    table, say -- silently rewrote the page as a side effect. It happened while
    counting how many photographs were cats. Harmless there because the output
    was identical, but an import that edits the site is a trap left lying about.
    """
    require_repo_root()
    path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    html = open(path, encoding='utf-8').read()

    block = ('  <!-- RAIL-BEGIN  generated by scratchpad/genrail.py; do not hand-edit -->\n'
             + markup() + '\n  <!-- RAIL-END -->')
    html, n = re.subn(r'  <!-- (?:WALL|RAIL)-BEGIN.*?<!-- (?:WALL|RAIL)-END -->',
                      lambda m: block, html, flags=re.S)
    if n != 1:
        sys.exit('rail markers: matched %d, expected 1' % n)

    # the old fixed wall had a caption describing slots that no longer exist
    html = re.sub(r'\n\s*<p class="cap">.*?</p>', '', html, flags=re.S)

    css = open(CSS_PATH, encoding='utf-8').read().rstrip('\n')
    marker = '  /* ------------------------------------------------------------- the signature -- */'
    html = re.sub(r'  /\* -+ the rail -- \*/.*?(?=  /\* -+ the signature -- \*/)', '', html, flags=re.S)
    if marker not in html:
        sys.exit('signature CSS marker not found')
    html = html.replace(marker, css + '\n\n' + marker, 1)

    anchor = '<script>\n/*  THE SINE EDGE ON THE CARDS'
    if '/*  THE WAVE FRAME ON THE PHOTOGRAPHS.' in html:
        html = re.sub(r'<script>\n/\*  THE WAVE FRAME ON THE PHOTOGRAPHS\..*?</script>\n\n', '', html, flags=re.S)
    if anchor not in html:
        sys.exit('card script anchor not found')
    html = html.replace(anchor, '<script>' + JS + '</script>\n\n' + anchor, 1)

    open(path, 'w', encoding='utf-8').write(html)
    print('rail spliced: %d photographs (%d wave, %d clips)'
          % (len(PHOTOS), sum(1 for p in PHOTOS if p[1] == 'wave'),
             sum(1 for p in PHOTOS if p[1] == 'clips')))


if __name__ == "__main__":
    main()
