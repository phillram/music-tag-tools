# music_tagger

A command-line utility for updating music file tags and renaming tracks based on their metadata.

**Supported formats:** MP3, FLAC, M4A/AAC (`.m4a`, `.mp4`), OGG Vorbis

---

## Installation

```bash
pip install mutagen
```

Or with the included requirements file:

```bash
pip install -r requirements.txt
```

---

## Usage

```
python music_tagger.py (--folder PATH | --file PATH) [OPTIONS]
```

At least one action option must be provided alongside a target.

---

## Target Selection

| Option | Short | Description |
|--------|-------|-------------|
| `--folder PATH` | `-f` | Process all supported audio files inside the given folder. |
| `--file PATH`   |      | Process a single audio file. |

These two options are mutually exclusive — you must provide exactly one.

---

## Options

### `--list` / `-l`

Display a table of all files in the target and their current tag values. No files are modified. Use this to inspect your files before running any update commands.

```bash
# List all files and tags in a folder
python music_tagger.py --folder /music/album --list

# List tags for a single file
python music_tagger.py --file /music/song.mp3 --list
```

Example output:

```
Filename                          Title           Artist         Album          Year  Disc  #   Genre
--------------------------------  --------------  -------------  ------------   ----  ----  --  -----
01 - Come Together.mp3            Come Together   The Beatles    Abbey Road     1969  1     1   Rock
02 - Something.mp3                Something       The Beatles    Abbey Road     1969  1     2   Rock
03 - Maxwell's Silver Hammer.mp3                  The Beatles    Abbey Road     1969  1     3
```

Fields with no value are shown as blank. `--list` exits immediately after printing and cannot be combined with any other option.

---

### `--recursive` / `-R`

Process all audio files in every subfolder nested inside the target folder. Without this flag only the immediate contents of `--folder` are processed.

- Only valid with `--folder`. Using `--recursive` with `--file` is an error.
- Files are processed folder-by-folder. A header is printed before each subfolder so you can follow progress in the console.
- All other options (`--rename`, `--tag`, `--tags-from-filename`, `--dry-run`, etc.) apply to every file found across all subfolders.
- Combine with `--list` to inspect an entire library before making changes.

```bash
# List all files and tags across an entire music library
python music_tagger.py --folder /music --recursive --list

# Set artist and album on all files in every subfolder
python music_tagger.py --folder /music/artist --recursive \
    --tag "artist=The Beatles"

# Rename every file across all subfolders using a pattern
python music_tagger.py --folder /music --recursive \
    --rename-pattern "{track} - {title}"

# Extract disc, track, and title from filenames like "1-01 - Come Together.mp3"
# across all subfolders, without modifying any files first
python music_tagger.py --folder /music/album --recursive \
    --tags-from-filename "{disc}-{track} - {title}" \
    --dry-run

# Replace underscores with spaces in titles across a whole library, then rename
python music_tagger.py --folder /music --recursive \
    --replace-special " " "_" \
    --rename
```

Example console output for a recursive run:

```
Found 6 file(s) across 2 folder(s) under '/music/artist'.

============================================================
Folder: disc1
============================================================

01 - Come Together.mp3
  tag artist = 'The Beatles'

02 - Something.mp3
  tag artist = 'The Beatles'

============================================================
Folder: disc2
============================================================

01 - Here Comes the Sun.mp3
  tag artist = 'The Beatles'
```

---

### `--rename` / `-r`

Rename each file so its filename matches its (possibly transformed) title tag. The original file extension is always preserved.

Characters that are illegal in filenames (`\ / : * ? " < > |`) are automatically replaced with `_` before renaming, so separators inside a title survive — a title of `Pokémon Sun/Moon` becomes `Pokémon Sun_Moon.mp3`, and `AC/DC` becomes `AC_DC`.

```bash
# Rename every file in a folder to match its embedded title tag
python music_tagger.py --folder /music/album --rename

# Rename a single file to match its title tag
python music_tagger.py --file /music/01_cool_song.mp3 --rename
```

| File on disk              | Title tag        | Result               |
|---------------------------|------------------|----------------------|
| `01_cool_song.mp3`        | `Cool Song`      | `Cool Song.mp3`      |
| `track02_-_hello.flac`    | `Hello`          | `Hello.flac`         |

---

### `--rename-pattern PATTERN`

Rename each file using a template string built from its tag values. Use curly-brace placeholders for any tag field.

**Available placeholders:** `{title}` `{artist}` `{album}` `{year}` `{track}` `{disc}` `{genre}`

- Missing or empty tags are substituted with an empty string, and take an adjacent separator with them — a file with no track number renames to `Title.mp3` under `{track:02} - {title}`, not `- Title.mp3`. Only separators next to an empty placeholder are removed, so a title that genuinely starts or ends with punctuation keeps it.
- The file extension is always preserved.
- Illegal filename characters are replaced with `_` automatically.
- `--rename-pattern` and `--rename` are mutually exclusive.

#### Zero-padding numbers

Append `:N` to a placeholder to zero-pad it to **N** digits. Without padding, a
25-track album sorts as 1, 10, 11, … 2, 20 — pad the track number to fix it.

```bash
# Zero-padded track number: "07 - Terminal March.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{track:02} - {title}"
```

| Pattern              | Track tag | Result             |
|----------------------|-----------|--------------------|
| `{track} - {title}`  | `7`       | `7 - Title.mp3`    |
| `{track:02} - {title}` | `7`     | `07 - Title.mp3`   |
| `{track:03} - {title}` | `7`     | `007 - Title.mp3`  |
| `{track:02} - {title}` | `12`    | `12 - Title.mp3`   |

Padding applies only to values that are entirely digits; any other value is
substituted unchanged. `--tags-from-filename` accepts the same `:N` syntax so a
single pattern string works in both directions, but ignores it when reading —
`{track:02}` captures `07` and `7` alike.

```bash
# Track number then title: "01 - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{track:02} - {title}"

# Artist then title: "The Beatles - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{artist} - {title}"

# Artist, album, and title: "The Beatles - Abbey Road - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{artist} - {album} - {title}"

# Year and title: "1969 - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{year} - {title}"

# Track number with dot separator: "01. Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{track}. {title}"

# Genre subfolder-style name: "Rock - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{genre} - {title}"
```

| Pattern                          | Tags                                        | Result filename                            |
|----------------------------------|---------------------------------------------|--------------------------------------------|
| `{track} - {title}`             | track=`01`, title=`Come Together`           | `01 - Come Together.mp3`                   |
| `{artist} - {title}`            | artist=`The Beatles`, title=`Come Together` | `The Beatles - Come Together.mp3`          |
| `{artist} - {album} - {title}`  | artist=`The Beatles`, album=`Abbey Road`, title=`Come Together` | `The Beatles - Abbey Road - Come Together.mp3` |
| `{year} - {title}`              | year=`1969`, title=`Come Together`          | `1969 - Come Together.mp3`                 |
| `{track}. {title}`              | track=`1`, title=`Come Together`            | `1. Come Together.mp3`                     |

> **Tip:** Combine `--rename-pattern` with `--tag` to set tags and rename in a single pass:
> ```bash
> python music_tagger.py --folder /music/album \
>     --tag "artist=The Beatles" \
>     --tag "album=Abbey Road" \
>     --rename-pattern "{track} - {title}"
> ```

---

### `--title-from-filename`

Set the title tag from the filename stem instead of reading it from existing metadata. This is the reverse of `--rename`.

All title transforms (`--strip-start`, `--strip-end`, `--remove-special`, `--replace-special`) are applied to the filename stem before the result is saved as the title tag.

- `--title-from-filename` and `--tags-from-filename` are mutually exclusive.

```bash
# Set the title tag directly from the filename stem, no transforms
python music_tagger.py --folder /music/album --title-from-filename

# Strip the first 3 characters of the filename before saving as title
# "01-Get Lucky.mp3" → title tag = "Get Lucky"
python music_tagger.py --folder /music/album --title-from-filename --strip-start 3

# Replace underscores with spaces in the filename, save as title
# "get_lucky.mp3" → title tag = "get lucky"
python music_tagger.py --folder /music/album --title-from-filename --replace-special " " "_"

# Strip a prefix AND replace underscores, then save as title and rename
# "01_get_lucky.mp3" → title tag = "get lucky", file = "get lucky.mp3"
python music_tagger.py --folder /music/album --title-from-filename --strip-start 3 --replace-special " " "_" --rename
```

| Filename              | Command                                      | Title tag set to  |
|-----------------------|----------------------------------------------|-------------------|
| `01-Get Lucky.mp3`    | `--title-from-filename --strip-start 3`      | `Get Lucky`       |
| `get_lucky.mp3`       | `--title-from-filename --replace-special " " "_"` | `get lucky`  |
| `Come Together.mp3`   | `--title-from-filename`                      | `Come Together`   |

---

### `--tags-from-filename PATTERN`

Parse the filename stem using a `{placeholder}` template to extract and set **multiple tags at once**. This is the reverse of `--rename-pattern`.

**Available placeholders:** `{title}` `{artist}` `{album}` `{year}` `{track}` `{disc}` `{genre}`

- The pattern must match the full filename stem.
- Non-final placeholders use non-greedy matching so adjacent segments are captured correctly.
- If the pattern does not match, a warning is printed and the file is skipped.
- `--tags-from-filename` and `--title-from-filename` are mutually exclusive.
- Title transforms (`--strip-start`, etc.) still apply to the extracted `{title}` portion.

```bash
# "01-Get Lucky.mp3" → track tag = "01", title tag = "Get Lucky"
python music_tagger.py --folder /music/album --tags-from-filename "{track}-{title}"

# "The Beatles - Come Together.mp3" → artist = "The Beatles", title = "Come Together"
python music_tagger.py --folder /music/album --tags-from-filename "{artist} - {title}"

# "The Beatles - Abbey Road - Come Together.mp3" → artist, album, and title all set
python music_tagger.py --folder /music/album --tags-from-filename "{artist} - {album} - {title}"

# "1969 - Come Together.mp3" → year = "1969", title = "Come Together"
python music_tagger.py --folder /music/album --tags-from-filename "{year} - {title}"

# "1-01 - Come Together.mp3" → disc = "1", track = "01", title = "Come Together"
python music_tagger.py --folder /music/album --tags-from-filename "{disc}-{track} - {title}"

# Extract tags from filename, then rename files using a different pattern
python music_tagger.py --folder /music/album \
    --tags-from-filename "{track} - {title}" \
    --rename-pattern "{artist} - {track} - {title}"
```

| Filename                                    | Pattern                         | Tags set                                        |
|---------------------------------------------|---------------------------------|-------------------------------------------------|
| `01-Get Lucky.mp3`                          | `{track}-{title}`               | track=`01`, title=`Get Lucky`                   |
| `The Beatles - Come Together.mp3`           | `{artist} - {title}`            | artist=`The Beatles`, title=`Come Together`     |
| `The Beatles - Abbey Road - Come Together.mp3` | `{artist} - {album} - {title}` | artist=`The Beatles`, album=`Abbey Road`, title=`Come Together` |
| `1969 - Come Together.mp3`                  | `{year} - {title}`              | year=`1969`, title=`Come Together`              |
| `1-01 - Come Together.mp3`                  | `{disc}-{track} - {title}`      | disc=`1`, track=`01`, title=`Come Together`     |

> **Tip:** Combine with `--tag` to set additional fields that aren't in the filename:
> ```bash
> python music_tagger.py --folder /music/album \
>     --tags-from-filename "{track} - {title}" \
>     --tag "artist=Daft Punk" \
>     --tag "album=Random Access Memories"
> ```

---

### `--tag KEY=VALUE` / `-t KEY=VALUE`

Set one or more tag fields. Repeat the flag for multiple tags. The tag is applied to every file in the target.

**Supported keys:** `title`, `artist`, `album`, `year`, `track`, `disc`, `genre`

```bash
# Set the artist and album on all files in a folder
python music_tagger.py --folder /music/album \
    --tag "artist=The Beatles" \
    --tag "album=Abbey Road"

# Set the year on a single file
python music_tagger.py --file /music/song.mp3 --tag "year=1969"

# Set the disc number on all files in a folder
python music_tagger.py --folder /music/disc1 --tag "disc=1"
```

---

### `--strip-start N`

Remove the first **N** characters from the title tag.

Useful for removing numeric prefixes or separators (e.g. `"01 - Song Name"` → `"Song Name"` with `--strip-start 5`).

```bash
# Remove the leading "01 - " (5 characters) from every title
python music_tagger.py --folder /music/album --strip-start 5 --rename
```

| Before           | `--strip-start 5` | After       |
|------------------|-------------------|-------------|
| `01 - Song Name` | Remove 5 chars    | `Song Name` |
| `02 - Track Two` | Remove 5 chars    | `Track Two` |

---

### `--strip-end N`

Remove the last **N** characters from the title tag.

```bash
# Remove a trailing " (Remaster)" suffix — 11 characters
python music_tagger.py --folder /music/album --strip-end 11 --rename
```

| Before                | `--strip-end 11` | After         |
|-----------------------|------------------|---------------|
| `Come Together (Remaster)` | Remove 11 chars | `Come Together` |

---

### `--remove-special [CHAR ...]`

Remove characters from the title.

- **No arguments** — removes every character that is not a letter, digit, or space.
- **With arguments** — removes only the specified characters.

```bash
# Remove ALL non-alphanumeric characters (spaces kept)
python music_tagger.py --folder /music/album --remove-special

# Remove only parentheses
python music_tagger.py --folder /music/album --remove-special "(" ")"

# Remove underscores and hyphens
python music_tagger.py --folder /music/album --remove-special "_" "-"
```

| Before                   | Command                          | After              |
|--------------------------|----------------------------------|--------------------|
| `(feat. Daft Punk)`      | `--remove-special "(" ")"`       | `feat. Daft Punk`  |
| `Rock!_Song-Title`       | `--remove-special`               | `Rock Song Title`  |
| `Track #5`               | `--remove-special "#"`           | `Track 5`          |

> **Note:** `--remove-special` and `--replace-special` cannot be used together.

---

### `--replace-special REPLACEMENT [CHAR ...]`

Replace characters in the title with a chosen replacement string.

- **First argument** — the replacement character or string (required).
- **No further arguments** — replaces every character that is not a letter, digit, or space.
- **Further arguments** — replaces only those specific characters.

```bash
# Replace underscores with spaces
python music_tagger.py --file /music/1_song_title.mp3 --replace-special " " "_"

# Replace underscores AND hyphens with spaces across a whole folder
python music_tagger.py --folder /music/album --replace-special " " "_" "-" --rename

# Replace ALL non-alphanumeric characters with a hyphen
python music_tagger.py --folder /music/album --replace-special "-"

# Replace dots with spaces
python music_tagger.py --folder /music/album --replace-special " " "."
```

| Before            | Command                                  | After             |
|-------------------|------------------------------------------|-------------------|
| `1_song_title`    | `--replace-special " " "_"`             | `1 song title`    |
| `Track.Name.Here` | `--replace-special " " "."`             | `Track Name Here` |
| `Song!@#Title`    | `--replace-special "-"`                 | `Song---Title`    |
| `My-Cool_Track`   | `--replace-special " " "-" "_"`         | `My Cool Track`   |

> **Note:** `--remove-special` and `--replace-special` cannot be used together.

---

### `--dry-run` / `-n`

Preview every change that *would* be made without modifying any files. No tags are written and no files are renamed.

Always recommended before running a batch operation on a large folder.

```bash
python music_tagger.py --folder /music/album \
    --strip-start 5 \
    --replace-special " " "_" \
    --rename \
    --dry-run
```

---

## Order of Operations

When multiple options are combined, they are applied in this order:

1. `--tag` explicit values are collected
2. `--tags-from-filename` extracts tags from the filename (merges with `--tag` values)
3. Working title is resolved:
   - `--title-from-filename` → filename stem
   - `--tags-from-filename` → extracted `{title}` value (if present)
   - Otherwise → `--tag title=...` → existing title tag → filename stem
4. `--strip-start` — removes N characters from the start of the working title
5. `--strip-end` — removes N characters from the end of the working title
6. `--remove-special` or `--replace-special` — character cleanup on the working title
7. Tag changes are written to the file
8. `--rename` — file renamed to the final title
   **or** `--rename-pattern` — file renamed using the pattern with all final tag values

---

## Combined Examples

```bash
# Strip "01 - " prefix, replace underscores with spaces, rename files, preview first
python music_tagger.py --folder /music/album \
    --strip-start 5 \
    --replace-special " " "_" \
    --rename \
    --dry-run

# Tag an entire album and rename all files in one command
python music_tagger.py --folder /music/album \
    --tag "artist=Pink Floyd" \
    --tag "album=The Dark Side of the Moon" \
    --tag "year=1973" \
    --strip-start 3 \
    --rename

# Fix a single badly-named file
python music_tagger.py --file "/music/01_-_come_together_(remaster).mp3" \
    --strip-start 5 \
    --strip-end 11 \
    --replace-special " " "_" \
    --rename

# Tag a multi-disc album: filenames like "1-01 - Come Together.mp3"
# Sets disc, track, and title from filename; sets artist and album manually
python music_tagger.py --folder /music/album \
    --tags-from-filename "{disc}-{track} - {title}" \
    --tag "artist=The Beatles" \
    --tag "album=Abbey Road"

# Same as above but also rename files to strip the disc prefix
python music_tagger.py --folder /music/album \
    --tags-from-filename "{disc}-{track} - {title}" \
    --tag "artist=The Beatles" \
    --tag "album=Abbey Road" \
    --rename-pattern "{track} - {title}"

# Inspect an entire library before making any changes
python music_tagger.py --folder /music --recursive --list

# Bulk-tag every file in a library: set genre, strip numeric prefix, rename
python music_tagger.py --folder /music --recursive \
    --tag "genre=Rock" \
    --strip-start 5 \
    --rename \
    --dry-run
```

---

## Supported Tag Keys

| Key      | Description               | Example value         |
|----------|---------------------------|-----------------------|
| `title`  | Track title               | `Come Together`       |
| `artist` | Track / performing artist | `The Beatles`         |
| `albumartist` | Artist the album is filed under | `The Beatles` |
| `album`  | Album name                | `Abbey Road`          |
| `year`   | Release year              | `1969`                |
| `track`  | Track number              | `1`                   |
| `disc`   | Disc number               | `1`                   |
| `genre`  | Genre                     | `Rock`                |

> **`albumartist` vs `artist`:** library managers group an album by `albumartist`.
> Leave it empty on a compilation and the album shatters into one entry per track
> artist. Set `artist` per track and `albumartist` once for the whole album —
> `--tag "albumartist=Various Artists"` is the usual fix.

Stored as `TPE2` in ID3, `albumartist` in FLAC and Ogg Vorbis, and `aART` in MP4.

If a tag key has no slot in the target format — or the file is a format this tool
cannot write — the write is reported and `write_tags` returns false, rather than
appearing to succeed while changing nothing.
