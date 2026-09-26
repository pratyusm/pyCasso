# pyCasso

**pyCasso** is a command-line ASCII art generator written in Python.

It converts images into terminal-friendly ASCII artwork with support for foreground isolation, true-color rendering, custom character palettes, clipboard output, and text export.

Turn this:

```text
portrait.jpg
```

into something considerably less practical:

```text
                  ...::::...
              .:-=++******++=-:.
           .-=+*###%%%%%%%%###*+=-.
         :=*##%%%%%%%%%%%%%%%%%%##*=:
       .=*#%%%%%%%%%%%%%%%%%%%%%%%%#*=.
      :+#%%%%%%%%%%%@@@@%%%%%%%%%%%%%#+:
     -*%%%%%%%%@@@@@@@@@@@@@@%%%%%%%%%%*-
```

Because apparently pixels weren't complicated enough.


## Features

- Convert common image formats into ASCII artwork
- Automatically resize artwork to fit the terminal
- Preserve the apparent aspect ratio of the source image
- Render monochrome ASCII directly in the terminal
- Render using 24-bit ANSI true color
- Automatically isolate image foregrounds using OpenCV GrabCut
- Disable foreground isolation when desired
- Use custom ASCII character palettes
- Invert brightness mapping
- Enable or disable histogram equalization
- Copy plain ASCII characters directly to the clipboard
- Copy rendered ASCII artwork as an image
- Copy rendered artwork in full color
- Export plain ASCII artwork to `.txt`
- Display information about generated artwork
- Combine rendering and output options


## Requirements

pyCasso requires:

- Python 3.10 or newer
- OpenCV
- NumPy
- Colorama
- Pyperclip
- Pillow

The image clipboard functionality currently targets **macOS**.


## Installation

### Install from the project

Clone or download the project and navigate to its root directory:

```bash
cd pyCasso
```

Install pyCasso in editable mode:

```bash
python3 -m pip install -e .
```

Editable installation is recommended during development because changes to the source code are immediately reflected in the installed command.

After installation, verify that pyCasso is available:

```bash
pycasso --help
```

You can also locate the installed command with:

```bash
which pycasso
```


## Project Structure

```text
pyCasso/
│
├── pyproject.toml
├── README.md
├── LICENSE
│
└── src/
    └── pycasso/
        ├── __init__.py
        └── cli.py
```

The command-line entry point is defined in `pyproject.toml`:

```toml
[project.scripts]
pycasso = "pycasso.cli:main"
```

This allows pyCasso to be run from anywhere using:

```bash
pycasso
```

rather than:

```bash
python3 pyCasso.py
```


# Usage

The basic syntax is:

```bash
pycasso IMAGE [WIDTH] [OPTIONS]
```

`IMAGE` is the path to the source image.

`WIDTH` is an optional maximum output width measured in ASCII characters.

For example:

```bash
pycasso portrait.jpg
```

or:

```bash
pycasso portrait.jpg 100
```


# Examples

## Basic ASCII Art

Convert an image using the default settings:

```bash
pycasso portrait.jpg
```

pyCasso automatically chooses an appropriate width based on the terminal, up to its default maximum of 120 characters.


## Set the Width

Specify the desired width after the image:

```bash
pycasso portrait.jpg 80
```

For a larger rendering:

```bash
pycasso portrait.jpg 120
```

The height is calculated automatically to preserve the apparent aspect ratio of the source image in a terminal.


## Color Output

Render the ASCII artwork using colors sampled from the original image:

```bash
pycasso portrait.jpg --color
```

The short form is:

```bash
pycasso portrait.jpg -c
```

pyCasso uses 24-bit ANSI foreground colors when displaying colored artwork in the terminal.


## Disable Foreground Isolation

By default, pyCasso attempts to isolate the foreground of the image using OpenCV's GrabCut algorithm.

To process the entire image instead:

```bash
pycasso portrait.jpg --no-isolate
```

This can be useful for landscapes, illustrations, scenes, or images where the background is an important part of the artwork.


## Custom Character Palettes

The default ASCII character palette is:

```text
 .:-=+*#%@
```

You can replace it using `--chars`:

```bash
pycasso portrait.jpg --chars " .oO@"
```

Characters are mapped according to image brightness.

For example:

```bash
pycasso portrait.jpg --chars " .:-=+*#%@"
```

or:

```bash
pycasso portrait.jpg --chars " 123456789"
```

The palette must contain at least two characters.


## Invert Brightness

Invert the brightness-to-character mapping:

```bash
pycasso portrait.jpg --invert
```

This can be useful when switching between light and dark backgrounds or experimenting with different character palettes.


## Disable Histogram Equalization

pyCasso applies histogram equalization by default to improve contrast before converting image brightness into characters.

Disable it with:

```bash
pycasso portrait.jpg --no-equalize
```

This preserves the original luminance distribution more closely.


# Clipboard Output

pyCasso supports two different clipboard modes:

- `--copy-text` copies the actual ASCII characters.
- `--copy` copies the rendered ASCII artwork as an image.

They intentionally behave differently.


## Copy ASCII Text

Copy the generated ASCII characters directly to the clipboard:

```bash
pycasso portrait.jpg --copy-text
```

The clipboard contains plain text only.

For best results, paste the output using a monospace font.


### Color and `--copy-text`

`--copy-text` always copies plain ASCII characters.

For example:

```bash
pycasso portrait.jpg --color --copy-text
```

displays colored ASCII in the terminal, but the clipboard still contains only plain ASCII text.

No ANSI escape sequences, HTML, or other color formatting are included in copied text.

This makes the result safe to paste into ordinary text editors.


## Copy as an Image

Copy the rendered ASCII artwork to the clipboard as an image:

```bash
pycasso portrait.jpg --copy
```

Without `--color`, the copied image contains black ASCII characters on a white background.

Because the clipboard contains an image rather than text, the artwork preserves its visual layout when pasted into applications that support image pasting.


## Copy a Colored Image

Combine `--color` and `--copy`:

```bash
pycasso portrait.jpg --color --copy
```

The terminal displays colored ASCII, and the clipboard receives a rendered image in which each ASCII character uses a color sampled from its corresponding source-image pixel.

The copied result remains ASCII art visually, but the characters are rendered into the image and are therefore no longer selectable as text.


## Clipboard Behavior

| Command               | Terminal         | Clipboard              |
|-----------------------|------------------|------------------------|
| `--copy-text`         | Monochrome ASCII | Plain ASCII text       |
| `--color --copy-text` | Colored ASCII    | Plain ASCII text       |
| `--copy`              | Monochrome ASCII | Monochrome ASCII image |
| `--color --copy`      | Colored ASCII    | Colored ASCII image    |

The `--color` flag never adds formatting or escape codes to `--copy-text` output.


# Text File Export

Save the generated ASCII artwork to a text file:

```bash
pycasso portrait.jpg --output portrait.txt
```

The short form is:

```bash
pycasso portrait.jpg -o portrait.txt
```

`--print` is also supported as an alias:

```bash
pycasso portrait.jpg --print portrait.txt
```

If no filename is supplied:

```bash
pycasso portrait.jpg --output
```

pyCasso saves the result as:

```text
pycasso.txt
```

If the specified filename has no extension:

```bash
pycasso portrait.jpg -o portrait
```

pyCasso automatically adds `.txt`.


## Color and Text Files

Text file output is always plain ASCII.

For example:

```bash
pycasso portrait.jpg --color -o portrait.txt
```

displays the artwork in color in the terminal while saving a clean, monochrome ASCII representation to `portrait.txt`.

ANSI color codes are not written to text files.


# Artwork Information

Use `--info` to display information about the generated artwork:

```bash
pycasso portrait.jpg --info
```

pyCasso reports information including:

```text
pyCasso output information
--------------------------
Source:       portrait.jpg
Width:        100 characters
Height:       42 lines
Color:        no
Isolation:    yes
Equalization: yes
Inverted:     no
Characters:   ' .:-=+*#%@'
```

This can be combined with other options:

```bash
pycasso portrait.jpg 100 --color --info
```


# Combining Options

Most pyCasso options can be combined.

For example:

```bash
pycasso portrait.jpg 100 --color --copy
```

renders the artwork at 100 characters wide, displays it in color, and copies a colored rendering to the clipboard.

Or:

```bash
pycasso portrait.jpg 80 --invert --copy-text
```

renders an inverted version and copies the resulting plain ASCII characters.

A more elaborate command might be:

```bash
pycasso portrait.jpg 100 \
    --color \
    --chars " .oO@" \
    --no-isolate \
    --copy \
    --output portrait.txt \
    --info
```

This:

1. renders the image at 100 characters wide,
2. uses source-image colors in the terminal,
3. uses ` .oO@` as the character palette,
4. disables foreground isolation,
5. copies the rendered colored ASCII image,
6. saves a plain-text version to `portrait.txt`, and
7. displays information about the result.


# Command Reference

## Positional Arguments

| Argument | Description                                 |
|----------|---------------------------------------------|
| `IMAGE`  | Path to the source image                    |
| `WIDTH`  | Optional maximum output width in characters |


## Rendering Options

| Option               | Description                                    |
|----------------------|------------------------------------------------|
| `-c`, `--color`      | Render using source-image colors               |
| `--no-isolate`       | Disable automatic foreground isolation         |
| `--chars CHARACTERS` | Set the characters used for brightness mapping |
| `--invert`           | Invert the ASCII brightness mapping            |
| `--no-equalize`      | Disable histogram equalization                 |


## Output Options

| Option                         | Description                                     |
|--------------------------------|-------------------------------------------------|
| `--copy-text`                  | Copy plain ASCII text to the clipboard          |
| `--copy`                       | Copy rendered ASCII artwork as an image         |
| `-o [FILE]`, `--output [FILE]` | Save plain ASCII artwork to a text file         |
| `--print [FILE]`               | Alias for `--output`                            |
| `--info`                       | Display information about the generated artwork |


## Help

Display the built-in command reference:

```bash
pycasso --help
```

or:

```bash
pycasso -h
```


# How pyCasso Works

pyCasso processes an image through several stages.


## 1. Image Loading

The source image is loaded using OpenCV.


## 2. Resizing

The image is resized to fit the requested output width.

If no width is specified, pyCasso uses the current terminal width, up to a maximum of 120 characters.

Because terminal characters are generally taller than they are wide, pyCasso applies an aspect-ratio correction when calculating the output height.


## 3. Foreground Isolation

Unless `--no-isolate` is supplied, pyCasso attempts to separate the primary subject from its background using OpenCV GrabCut.

The isolated subject is placed against a white background.

Foreground isolation works best when the main subject is reasonably distinct from its surroundings.


## 4. Grayscale Conversion

The processed image is converted to grayscale.

By default, histogram equalization is applied to increase contrast.

Use:

```bash
--no-equalize
```

to disable this behavior.


## 5. Character Mapping

Each grayscale pixel is mapped to a character in the active ASCII palette.

The default palette is:

```text
 .:-=+*#%@
```

Different brightness levels therefore produce different characters.


## 6. Color Rendering

When `--color` is enabled, pyCasso samples the corresponding RGB color from the source image.

For terminal output, that color is represented using 24-bit ANSI escape sequences.

For copied image output, the ASCII character itself is rendered using the sampled RGB color.


## 7. Output

The result can then be:

- displayed in the terminal,
- copied as plain ASCII text,
- copied as a rendered image,
- saved as a text file, or
- used with several of those outputs simultaneously.


# Supported Images

pyCasso uses OpenCV for image loading, so it works with commonly supported raster image formats such as:

```text
.jpg
.jpeg
.png
.bmp
.tiff
.webp
```

Actual format support depends on the OpenCV build installed on the system.


# Tips for Better Results

ASCII conversion works best when the source image has:

- a clearly defined subject,
- good contrast,
- recognizable silhouettes,
- useful differences between light and dark regions,
- enough resolution to preserve important details.

Portraits, objects, architecture, logos, and high-contrast illustrations are particularly suitable.

If the result looks too noisy, try reducing the width:

```bash
pycasso image.jpg 60
```

If important detail is missing, increase it:

```bash
pycasso image.jpg 120
```

If foreground isolation removes useful parts of the image:

```bash
pycasso image.jpg --no-isolate
```

If the contrast looks unnatural:

```bash
pycasso image.jpg --no-equalize
```

If the light and dark regions appear backwards for your terminal:

```bash
pycasso image.jpg --invert
```

Experimenting with `--chars` can also dramatically change the appearance of the result:

```bash
pycasso image.jpg --chars " .oO@"
```


# Development

Install the package in editable mode:

```bash
python3 -m pip install -e .
```

The package uses a `src` layout:

```text
src/
└── pycasso/
    ├── __init__.py
    └── cli.py
```

After editable installation, changes made to `src/pycasso/cli.py` are reflected when running:

```bash
pycasso
```

without reinstalling the package after every edit.


## Run Without the Installed Command

During development, the CLI module can also be executed directly:

```bash
python3 src/pycasso/cli.py image.jpg
```

However, testing through the installed `pycasso` command is recommended because it also verifies that the package entry point is configured correctly.


# Dependencies

pyCasso currently uses:

### OpenCV

Used for:

- image loading,
- resizing,
- grayscale conversion,
- histogram equalization,
- foreground isolation.

### NumPy

Used for image and mask manipulation during foreground isolation.

### Colorama

Used to support terminal color handling.

### Pyperclip

Used for copying plain ASCII text to the system clipboard.

### Pillow

Used to render ASCII characters into images for image clipboard output.


# Platform Notes

## macOS

pyCasso's rendered-image clipboard functionality currently uses macOS clipboard facilities.

Commands such as:

```bash
pycasso image.jpg --copy
```

and:

```bash
pycasso image.jpg --color --copy
```

therefore currently target macOS.

Plain-text copying through:

```bash
pycasso image.jpg --copy-text
```

uses Pyperclip and may work on additional platforms depending on the system clipboard environment.


# Troubleshooting

## `pycasso: command not found`

Make sure the package has been installed:

```bash
python3 -m pip install -e .
```

Then check:

```bash
which pycasso
```

If multiple Python installations are present, verify which interpreter and pip installation are being used:

```bash
which python3
python3 -m pip --version
```


## Image Cannot Be Read

If pyCasso reports:

```text
Could not read image
```

verify that:

- the path is correct,
- the file exists,
- the file is a supported image format,
- the current user has permission to read it.


## Foreground Isolation Looks Wrong

Foreground isolation is automatic and cannot perfectly identify the subject of every image.

Disable it with:

```bash
pycasso image.jpg --no-isolate
```


## Copied Text Loses Its Shape

ASCII artwork depends on fixed character widths.

Paste it using a monospace font such as:

```text
Menlo
Monaco
Consolas
Courier New
```

Proportional fonts give every character a different width and consequently turn carefully arranged ASCII artwork into typographical wreckage.


## Terminal Colors Do Not Appear

`--color` requires a terminal capable of displaying 24-bit ANSI true color.

Try:

```bash
pycasso image.jpg --color
```

in a modern terminal emulator.


# Version

Current version:

```text
1.0.5
```


# License

Copyright © 2026 Pratyus Mohapatra.

pyCasso is free software licensed under the **GNU Affero General Public
License v3.0 or later (AGPL-3.0-or-later)**.

See [LICENSE](LICENSE) for the complete license terms.