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

### `--rename` / `-r`

Rename each file so its filename matches its (possibly transformed) title tag. The original file extension is always preserved.

Characters that are illegal in filenames (`\ / : * ? " < > |`) are automatically stripped before renaming.

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

**Available placeholders:** `{title}` `{artist}` `{album}` `{year}` `{track}` `{genre}`

- Missing or empty tags are substituted with an empty string.
- The file extension is always preserved.
- Illegal filename characters are stripped automatically.
- `--rename-pattern` and `--rename` are mutually exclusive.

```bash
# Track number then title: "01 - Come Together.mp3"
python music_tagger.py --folder /music/album --rename-pattern "{track} - {title}"

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

### `--tag KEY=VALUE` / `-t KEY=VALUE`

Set one or more tag fields. Repeat the flag for multiple tags. The tag is applied to every file in the target.

**Supported keys:** `title`, `artist`, `album`, `year`, `track`, `genre`

```bash
# Set the artist and album on all files in a folder
python music_tagger.py --folder /music/album \
    --tag "artist=The Beatles" \
    --tag "album=Abbey Road"

# Set the year on a single file
python music_tagger.py --file /music/song.mp3 --tag "year=1969"
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

When multiple transform options are combined, they are applied in this order:

1. `--tag` values are applied (an explicit `--tag title=...` becomes the working title)
2. `--strip-start` — removes N characters from the start of the title
3. `--strip-end` — removes N characters from the end of the title
4. `--remove-special` or `--replace-special` — character cleanup on the title
5. `--rename` — file renamed to the final title
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
```

---

## Supported Tag Keys

| Key      | Description              | Example value         |
|----------|--------------------------|-----------------------|
| `title`  | Track title              | `Come Together`       |
| `artist` | Track / performing artist| `The Beatles`         |
| `album`  | Album name               | `Abbey Road`          |
| `year`   | Release year             | `1969`                |
| `track`  | Track number             | `1`                   |
| `genre`  | Genre                    | `Rock`                |
