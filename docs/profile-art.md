# Profile art pipeline

Same terminal aesthetic as the Avi-style README: animated ASCII portrait,
3D ASCII wordmark, and a live contribution heatmap.

## One-time / when you change your photo

1. Put your portrait at `source-photo.jpg` (clear face photo works best).
2. Rebuild the ASCII SVG:

```bash
python scripts/prep_photo.py
python scripts/make_ascii_svg.py
```

Or pull your current GitHub avatar first:

```bash
python scripts/fetch_avatar.py
python scripts/prep_photo.py
python scripts/make_ascii_svg.py
```

## Wordmark (PRATHAM)

```bash
python scripts/make_wordmark_svg.py --mode rock --out wordmark.svg
```

## Contribution graph (dynamic)

Runs daily via `.github/workflows/update-profile-art.yml`. Manually:

```bash
python scripts/fetch_contributions.py
python scripts/generate_streak_svg.py prathampateliya123 contrib-heatmap.svg
```

## Dependencies

```bash
pip install -r scripts/requirements.txt
# optional better portrait cutout:
pip install rembg opencv-python-headless
```
