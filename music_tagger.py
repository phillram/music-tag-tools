#!/usr/bin/env python3
"""
music_tagger.py - A utility for updating music file tags and filenames.

Supports: MP3, FLAC, M4A/AAC, OGG Vorbis
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TCON, TPOS, ID3NoHeaderError
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
except ImportError:
    print("Error: mutagen is required. Run: pip install mutagen")
    sys.exit(1)

SUPPORTED_FORMATS = {".mp3", ".flac", ".m4a", ".mp4", ".ogg"}


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def get_audio_files(path: Path, recursive: bool = False) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_FORMATS:
            return [path]
        print(f"Error: '{path.name}' is not a supported audio format.")
        sys.exit(1)
    if path.is_dir():
        glob = path.rglob if recursive else path.glob
        files = []
        for fmt in SUPPORTED_FORMATS:
            files.extend(glob(f"*{fmt}"))
            files.extend(glob(f"*{fmt.upper()}"))
        return sorted(set(files))
    print(f"Error: '{path}' does not exist.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Tag reading
# ---------------------------------------------------------------------------

def read_tags(file_path: Path) -> dict:
    """Return a dict with keys: title, artist, album, year, track, disc, genre."""
    tags = {k: "" for k in ("title", "artist", "album", "year", "track", "disc", "genre")}
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".mp3":
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                return tags
            tags["title"]  = str(audio.get("TIT2", ""))
            tags["artist"] = str(audio.get("TPE1", ""))
            tags["album"]  = str(audio.get("TALB", ""))
            tags["year"]   = str(audio.get("TDRC", ""))
            tags["track"]  = str(audio.get("TRCK", ""))
            tags["disc"]   = str(audio.get("TPOS", ""))
            tags["genre"]  = str(audio.get("TCON", ""))

        elif suffix == ".flac":
            audio = FLAC(file_path)
            tags["title"]  = audio.get("title",       [""])[0]
            tags["artist"] = audio.get("artist",      [""])[0]
            tags["album"]  = audio.get("album",       [""])[0]
            tags["year"]   = audio.get("date",        [""])[0]
            tags["track"]  = audio.get("tracknumber", [""])[0]
            tags["disc"]   = audio.get("discnumber",  [""])[0]
            tags["genre"]  = audio.get("genre",       [""])[0]

        elif suffix in (".m4a", ".mp4"):
            audio = MP4(file_path)
            tags["title"]  = audio.get("\xa9nam", [""])[0]
            tags["artist"] = audio.get("\xa9ART", [""])[0]
            tags["album"]  = audio.get("\xa9alb", [""])[0]
            tags["year"]   = audio.get("\xa9day", [""])[0]
            tags["genre"]  = audio.get("\xa9gen", [""])[0]
            trkn = audio.get("trkn", [(0, 0)])
            tags["track"]  = str(trkn[0][0]) if trkn and trkn[0][0] else ""
            disk = audio.get("disk", [(0, 0)])
            tags["disc"]   = str(disk[0][0]) if disk and disk[0][0] else ""

        elif suffix == ".ogg":
            audio = OggVorbis(file_path)
            tags["title"]  = audio.get("title",       [""])[0]
            tags["artist"] = audio.get("artist",      [""])[0]
            tags["album"]  = audio.get("album",       [""])[0]
            tags["year"]   = audio.get("date",        [""])[0]
            tags["track"]  = audio.get("tracknumber", [""])[0]
            tags["disc"]   = audio.get("discnumber",  [""])[0]
            tags["genre"]  = audio.get("genre",       [""])[0]

    except Exception as exc:
        print(f"  Warning: Could not read tags from '{file_path.name}': {exc}")

    return tags


# ---------------------------------------------------------------------------
# Tag writing
# ---------------------------------------------------------------------------

def write_tags(file_path: Path, updates: dict, dry_run: bool) -> bool:
    suffix = file_path.suffix.lower()

    if dry_run:
        for key, value in updates.items():
            print(f"  [dry-run] tag {key} = {value!r}")
        return True

    try:
        if suffix == ".mp3":
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()
            frame_map = {
                "title":  TIT2, "artist": TPE1, "album": TALB,
                "year":   TDRC, "track":  TRCK, "disc":  TPOS, "genre": TCON,
            }
            for key, value in updates.items():
                if key in frame_map:
                    cls = frame_map[key]
                    audio[cls.__name__] = cls(encoding=3, text=value)
            audio.save(file_path)

        elif suffix == ".flac":
            audio = FLAC(file_path)
            key_map = {
                "title": "title", "artist": "artist", "album": "album",
                "year": "date", "track": "tracknumber", "disc": "discnumber", "genre": "genre",
            }
            for key, value in updates.items():
                if key in key_map:
                    audio[key_map[key]] = value
            audio.save()

        elif suffix in (".m4a", ".mp4"):
            audio = MP4(file_path)
            key_map = {
                "title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb",
                "year": "\xa9day", "genre": "\xa9gen",
            }
            for key, value in updates.items():
                if key == "disc":
                    try:
                        audio["disk"] = [(int(value), 0)]
                    except ValueError:
                        print(f"  Warning: disc value '{value}' is not a number — skipping")
                elif key in key_map:
                    audio[key_map[key]] = [value]
            audio.save()

        elif suffix == ".ogg":
            audio = OggVorbis(file_path)
            key_map = {
                "title": "title", "artist": "artist", "album": "album",
                "year": "date", "track": "tracknumber", "disc": "discnumber", "genre": "genre",
            }
            for key, value in updates.items():
                if key in key_map:
                    audio[key_map[key]] = value
            audio.save()

        for key, value in updates.items():
            print(f"  tag {key} = {value!r}")
        return True

    except Exception as exc:
        print(f"  Error writing tags to '{file_path.name}': {exc}")
        return False


# ---------------------------------------------------------------------------
# Title transformations
# ---------------------------------------------------------------------------

def apply_transforms(title: str, args: argparse.Namespace) -> str:
    """Apply strip / special-char transforms to a title string in order."""

    # 1. Strip characters from the start
    if args.strip_start:
        title = title[args.strip_start:]

    # 2. Strip characters from the end
    if args.strip_end:
        title = title[: -args.strip_end] if args.strip_end < len(title) else ""

    # 3a. Remove special characters
    if args.remove_special is not None:
        if args.remove_special:
            # Remove only the explicitly listed characters
            for ch in args.remove_special:
                title = title.replace(ch, "")
        else:
            # Remove all non-alphanumeric characters (spaces are kept)
            title = re.sub(r"[^a-zA-Z0-9 ]", "", title)

    # 3b. Replace special characters
    elif args.replace_special is not None:
        replacement = args.replace_special[0]
        targets = args.replace_special[1:]
        if targets:
            for ch in targets:
                title = title.replace(ch, replacement)
        else:
            # Replace all non-alphanumeric characters (spaces are kept)
            title = re.sub(r"[^a-zA-Z0-9 ]", replacement, title)

    return title.strip()


# ---------------------------------------------------------------------------
# File renaming
# ---------------------------------------------------------------------------

PATTERN_KEYS = ("title", "artist", "album", "year", "track", "disc", "genre")


def build_filename_from_pattern(pattern: str, tags: dict) -> str:
    """
    Substitute {title}, {artist}, {album}, {year}, {track}, {genre} in pattern.
    Missing tags are replaced with an empty string.
    """
    result = pattern
    for key in PATTERN_KEYS:
        result = result.replace(f"{{{key}}}", tags.get(key, ""))
    return result


def parse_filename_pattern(pattern: str, stem: str) -> dict:
    """
    Extract tag values from a filename stem using a {key} template pattern.
    Returns a dict of {tag_key: value}. Returns {} if the pattern does not match.
    """
    keys = re.findall(r"\{(\w+)\}", pattern)
    if not keys:
        return {}

    duplicates = [k for k in keys if keys.count(k) > 1]
    if duplicates:
        print(f"  Warning: duplicate placeholder(s) in pattern: {set(duplicates)} — skipping")
        return {}

    # Escape the literal parts of the pattern, then restore placeholders as
    # named capture groups. Non-final groups use non-greedy matching so that
    # adjacent segments don't bleed into each other.
    escaped = re.escape(pattern)
    for i, key in enumerate(keys):
        escaped_ph = re.escape(f"{{{key}}}")
        group = f"(?P<{key}>.+?)" if i < len(keys) - 1 else f"(?P<{key}>.+)"
        escaped = escaped.replace(escaped_ph, group, 1)

    match = re.fullmatch(escaped, stem)
    if not match:
        return {}

    result = {}
    for key in keys:
        if key not in PATTERN_KEYS:
            print(f"  Warning: unknown tag key '{{{key}}}' in pattern — skipping")
            continue
        result[key] = match.group(key).strip()

    return result


def rename_file(file_path: Path, new_stem: str, dry_run: bool) -> Path:
    """Rename file_path using new_stem, preserving the extension."""
    # Sanitise: remove characters that are illegal in Windows/POSIX filenames
    safe_stem = re.sub(r'[\\/:*?"<>|]', "", new_stem).strip()
    if not safe_stem:
        print("  Warning: filename is empty after sanitisation — skipping rename.")
        return file_path

    new_path = file_path.parent / (safe_stem + file_path.suffix)

    if new_path == file_path:
        return file_path  # nothing to do

    if dry_run:
        print(f"  [dry-run] rename '{file_path.name}' -> '{new_path.name}'")
        return new_path

    if new_path.exists():
        print(f"  Warning: '{new_path.name}' already exists — skipping rename.")
        return file_path

    file_path.rename(new_path)
    print(f"  renamed '{file_path.name}' -> '{new_path.name}'")
    return new_path


# ---------------------------------------------------------------------------
# Listing / inspection
# ---------------------------------------------------------------------------

COLUMNS = ("filename", "title", "artist", "album", "year", "disc", "track", "genre")
COL_HEADERS = {
    "filename": "Filename", "title": "Title", "artist": "Artist",
    "album": "Album", "year": "Year", "disc": "Disc", "track": "#", "genre": "Genre",
}


def list_files(files: list[Path]) -> None:
    """Print a formatted table of filename + all tags to stdout."""
    rows = []
    for f in files:
        tags = read_tags(f)
        rows.append({
            "filename": f.name,
            "title":    tags["title"],
            "artist":   tags["artist"],
            "album":    tags["album"],
            "year":     tags["year"],
            "track":    tags["track"],
            "genre":    tags["genre"],
        })

    # Calculate column widths: max of header and all cell values
    widths = {col: len(COL_HEADERS[col]) for col in COLUMNS}
    for row in rows:
        for col in COLUMNS:
            widths[col] = max(widths[col], len(row[col]))

    def fmt_row(row: dict) -> str:
        return "  ".join(row[col].ljust(widths[col]) for col in COLUMNS).rstrip()

    separator = "  ".join("-" * widths[col] for col in COLUMNS)
    header = fmt_row(COL_HEADERS)

    print(header)
    print(separator)
    for row in rows:
        print(fmt_row(row))
    print(f"\n{len(rows)} file(s) found.")


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_file(file_path: Path, args: argparse.Namespace) -> None:
    print(f"\n{file_path.name}")

    existing = read_tags(file_path)
    updates: dict[str, str] = {}

    # Explicit --tag overrides
    if args.tag:
        for pair in args.tag:
            if "=" not in pair:
                print(f"  Warning: invalid --tag value '{pair}' (expected key=value)")
                continue
            key, _, value = pair.partition("=")
            key = key.lower().strip()
            if key not in ("title", "artist", "album", "year", "track", "disc", "genre"):
                print(f"  Warning: unknown tag key '{key}' — skipping")
                continue
            updates[key] = value.strip()

    # Tags sourced from filename pattern (--tags-from-filename)
    if args.tags_from_filename:
        extracted = parse_filename_pattern(args.tags_from_filename, file_path.stem)
        if not extracted:
            print(f"  Warning: pattern did not match '{file_path.stem}' — skipping tag extraction")
        else:
            for key, value in extracted.items():
                print(f"  from filename: {key} = {value!r}")
            updates.update(extracted)

    # Determine working title:
    #   --title-from-filename  → always use the filename stem as the source
    #   --tags-from-filename   → use the extracted title if present
    #   otherwise              → --tag title > existing title tag > filename stem
    if args.title_from_filename:
        title = file_path.stem
    else:
        title = updates.get("title") or existing["title"] or file_path.stem

    # Apply title transforms if requested
    needs_transform = any([
        args.strip_start,
        args.strip_end,
        args.remove_special is not None,
        args.replace_special is not None,
    ])

    if needs_transform or args.title_from_filename:
        transformed = apply_transforms(title, args)
        if transformed != title:
            print(f"  title transform: {title!r} -> {transformed!r}")
        updates["title"] = transformed
        title = transformed
    elif "title" not in updates:
        # --tags-from-filename may have set it; keep whatever is in updates
        title = updates.get("title", title)

    # Write tag changes
    if updates:
        write_tags(file_path, updates, args.dry_run)

    # Rename file
    if args.rename_pattern:
        # Merge existing tags with any updates so the pattern sees the final values
        merged = {**existing, **updates}
        stem = build_filename_from_pattern(args.rename_pattern, merged)
        rename_file(file_path, stem, args.dry_run)
    elif args.rename:
        rename_file(file_path, title, args.dry_run)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="music_tagger",
        description="Update music file tags and filenames (MP3, FLAC, M4A, OGG).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rename all files in a folder to match their title tag
  python music_tagger.py --folder /music/album --rename

  # Rename using a pattern: "01 - Come Together.mp3"
  python music_tagger.py --folder /music/album --rename-pattern "{track} - {title}"

  # Set artist and album on every file in a folder
  python music_tagger.py --folder /music/album --tag "artist=The Beatles" --tag "album=Abbey Road"

  # Strip a 5-character prefix like "01 - " from every title
  python music_tagger.py --folder /music/album --strip-start 5 --rename

  # Strip a 5-character suffix from every title
  python music_tagger.py --folder /music/album --strip-end 5

  # Replace underscores with spaces in a single file's title
  python music_tagger.py --file /music/1_song_title.mp3 --replace-special " " "_" --rename

  # Replace underscores AND hyphens with spaces across a folder
  python music_tagger.py --folder /music/album --replace-special " " "_" "-" --rename

  # Replace ALL non-alphanumeric characters with spaces
  python music_tagger.py --folder /music/album --replace-special " " --rename

  # Remove specific characters from titles outright
  python music_tagger.py --folder /music/album --remove-special "(" ")"

  # Remove ALL non-alphanumeric characters (spaces kept)
  python music_tagger.py --folder /music/album --remove-special

  # Set title tag from filename stem
  python music_tagger.py --folder /music/album --title-from-filename

  # Set title tag from filename, stripping a 3-char prefix first
  python music_tagger.py --folder /music/album --title-from-filename --strip-start 3

  # Parse filename pattern to set track number and title tags
  python music_tagger.py --folder /music/album --tags-from-filename "{track} - {title}"

  # Parse disc and track from filename: "1-01 - Come Together"
  python music_tagger.py --folder /music/album --tags-from-filename "{disc}-{track} - {title}"

  # Set disc number manually
  python music_tagger.py --folder /music/disc1 --tag "disc=1"

  # Parse artist and title from filename, then rename using a different pattern
  python music_tagger.py --folder /music/album --tags-from-filename "{artist} - {title}" --rename-pattern "{artist} - {title}"

  # List all files and their current tags (no modifications)
  python music_tagger.py --folder /music/album --list

  # Process all nested subfolders recursively
  python music_tagger.py --folder /music --recursive --tag "artist=The Beatles"

  # Recursive rename using a pattern across an entire library
  python music_tagger.py --folder /music --recursive --rename-pattern "{track} - {title}"

  # Recursive dry run to preview changes across all subfolders
  python music_tagger.py --folder /music --recursive --strip-start 3 --rename --dry-run

  # Dry run: preview every change without touching files
  python music_tagger.py --folder /music/album --strip-start 3 --rename --dry-run
        """,
    )

    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--folder", "-f", type=Path, metavar="PATH",
                        help="Process all audio files inside this folder.")
    target.add_argument("--file", type=Path, metavar="PATH",
                        help="Process a single audio file.")

    rename_group = parser.add_mutually_exclusive_group()
    rename_group.add_argument(
        "--rename", "-r", action="store_true",
        help="Rename the file to match the (possibly transformed) title tag.",
    )
    rename_group.add_argument(
        "--rename-pattern", metavar="PATTERN",
        help=("Rename the file using a template built from tag placeholders. "
              "Available placeholders: {title} {artist} {album} {year} {track} {genre}. "
              "Example: --rename-pattern \"{track} - {title}\""),
    )

    from_filename_group = parser.add_mutually_exclusive_group()
    from_filename_group.add_argument(
        "--title-from-filename", action="store_true",
        help=("Set the title tag from the filename stem. "
              "Transforms (--strip-start, --strip-end, --remove-special, --replace-special) "
              "are applied to the filename stem before saving."),
    )
    from_filename_group.add_argument(
        "--tags-from-filename", metavar="PATTERN",
        help=("Parse the filename stem using a template to extract and set multiple tags. "
              "Available placeholders: {title} {artist} {album} {year} {track} {genre}. "
              "Example: --tags-from-filename \"{track} - {title}\""),
    )

    parser.add_argument("--tag", "-t", action="append", metavar="KEY=VALUE",
                        help=("Set a tag. Repeatable. "
                              "Keys: title, artist, album, year, track, disc, genre. "
                              "Example: --tag \"artist=Daft Punk\""))

    parser.add_argument("--strip-start", type=int, metavar="N",
                        help="Remove the first N characters from the title.")
    parser.add_argument("--strip-end", type=int, metavar="N",
                        help="Remove the last N characters from the title.")

    special = parser.add_mutually_exclusive_group()
    special.add_argument(
        "--remove-special", nargs="*", metavar="CHAR",
        help=("Remove characters from the title. "
              "No args: removes every non-alphanumeric character (spaces kept). "
              "With args: removes only those specific characters. "
              "Example: --remove-special \"(\" \")\""),
    )
    special.add_argument(
        "--replace-special", nargs="+", metavar=("REPLACEMENT", "CHAR"),
        help=("Replace characters in the title. "
              "First argument is the replacement string. "
              "No further args: replaces every non-alphanumeric character (spaces kept). "
              "Further args: replaces only those specific characters. "
              "Example: --replace-special \" \" \"_\" \"-\""),
    )

    parser.add_argument("--recursive", "-R", action="store_true",
                        help=("Process all subfolders inside the target folder recursively. "
                              "Only valid with --folder. Each subfolder's files are listed "
                              "and processed as a group."))

    parser.add_argument("--list", "-l", action="store_true",
                        help=("Display a table of all files and their current tags. "
                              "No files are modified. Cannot be combined with other options."))

    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would change without modifying any files.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.recursive and args.file:
        parser.error("--recursive can only be used with --folder, not --file.")

    target = args.folder or args.file
    files = get_audio_files(target, recursive=getattr(args, "recursive", False))

    if not files:
        print("No supported audio files found.")
        sys.exit(0)

    if args.list:
        list_files(files)
        sys.exit(0)

    if args.dry_run:
        print("=== DRY RUN — no files will be modified ===")

    if args.recursive:
        # Group by parent directory and process each folder in turn
        folders: dict[Path, list[Path]] = {}
        for f in files:
            folders.setdefault(f.parent, []).append(f)

        total = sum(len(v) for v in folders.values())
        print(f"Found {total} file(s) across {len(folders)} folder(s) under '{target}'.")

        for folder, folder_files in sorted(folders.items()):
            rel = folder.relative_to(target)
            print(f"\n{'='*60}")
            print(f"Folder: {rel if str(rel) != '.' else '(root)'}")
            print(f"{'='*60}")
            for file_path in sorted(folder_files):
                process_file(file_path, args)
    else:
        print(f"Found {len(files)} file(s) in '{target}'.")
        for file_path in files:
            process_file(file_path, args)

    print("\nDone.")


if __name__ == "__main__":
    main()
