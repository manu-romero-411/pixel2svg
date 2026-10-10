# pixelart2svg

Convert pixel art (PNG) into a pixel-perfect vector SVG: **one `<path>` per colour**, integer coordinates only
(1 SVG unit = 1 sprite pixel). The result is verified against the source image before the script finishes.

## Install

```
pip install -r requirements.txt     # Pillow + numpy
```

Python 3.8 or newer. No other dependencies, no network access needed.

## Usage

```
python3 pixelart2svg.py sprite.png                   # -> sprite.svg
python3 pixelart2svg.py sprite.png out.svg --scale 13
python3 pixelart2svg.py upscaled.png --cell 13       # PNG already enlarged in 13x13 blocks
python3 pixelart2svg.py sprite.png --disjoint        # shapes without overlaps
```

| Option | Meaning |
|---|---|
| `--scale N` | Output size in px per sprite pixel (SVG `width`/`height`). Default `1`. |
| `--cell N` | Source PNG is an upscaled sprite in NxN blocks; the centre of each block is sampled. |
| `--disjoint` | Each shape holds only its own pixels. Easier to edit, but a hairline gap may appear between colours when scaled. |
| `--no-verify` | Skip the pixel-by-pixel check. |

Expected output: `verification: 0 of 1520 pixels differ -> PIXEL-PERFECT`.

## How it works

1. Build the palette: every distinct RGBA value becomes one shape (fully transparent pixels are ignored).
2. Make a boolean mask per colour.
3. Trace the mask outline: every pixel side facing "outside" is a directed edge with the interior on its right,
   so outer contours and holes get opposite winding with no special cases.
4. Chain the edges into closed loops. At a vertex with two exits (pixels touching only at a corner) always turn right,
   which keeps diagonal pixels separate.
5. Remove collinear points and write one `<path fill-rule="evenodd">` per colour.
6. Order shapes by area, largest first. In the default *underlay* mode each shape also includes the pixels of the shapes
   painted after it, so anti-aliasing never exposes seams between neighbouring colours; every pixel is still painted
   last by its own colour, so the picture is identical. Recolouring a colour only needs a change of its `fill`.
7. Rasterise the SVG and compare it pixel by pixel with the PNG.

## Limits

- Needs real pixel art. Anti-aliased, blurred or JPEG-compressed images produce one shape per intermediate tone;
  reduce them first to their native resolution with nearest-neighbour scaling.
- Semi-transparent pixels are supported (as `fill-opacity`) but force `--disjoint`.
- Large, heavily dithered images create large files.
- Output uses only `path`, `fill` and `fill-rule`, so it also renders in NanoSVG (the rasteriser used by EmulationStation).
