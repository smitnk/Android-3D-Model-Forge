# Gorilla reference (owner-supplied)

Cropped from the turnaround sheet supplied by the repository owner. Used by `scripts/gorilla.py`:

- `tpose-front.png`, `tpose-back.png` — T-pose panels, centred on the body axis and made symmetric
  (alpha = figure mask = the model's front silhouette). RGB is projected onto the model: where mirroring
  adds figure the drawing lacks, the mirrored pixels are used; the drawn outline within 3 px of the
  silhouette is replaced with interior colour, and the background is filled with the nearest figure colour,
  so faces seen at grazing angles do not smear black lines.
- `side-right.png` — 90° view; alpha = figure mask, used for the body's depth profile.
