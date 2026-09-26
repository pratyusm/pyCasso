# pyCasso - A command-line ASCII art generator.
# Copyright (C) 2026 Pratyus Mohapatra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from colorama import init
from PIL import Image, ImageDraw, ImageFont

init()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASCII_CHARS = " .:-=+*#%@"
RESET = "\033[0m"

DEFAULT_MAX_WIDTH = 120
DEFAULT_OUTPUT_FILE = "pycasso.txt"

# Image rendering settings
IMAGE_FONT_SIZE = 16
IMAGE_PADDING = 20
IMAGE_BACKGROUND = (255, 255, 255)
IMAGE_FOREGROUND = (0, 0, 0)


# ---------------------------------------------------------------------------
# ANSI Color
# ---------------------------------------------------------------------------

def rgb_to_ansi(r, g, b):
    """Return a 24-bit ANSI foreground color escape sequence."""
    return f"\033[38;2;{r};{g};{b}m"


# ---------------------------------------------------------------------------
# Image Processing
# ---------------------------------------------------------------------------

def resize_for_terminal(image, max_width=None):
    """
    Resize an image for terminal display.

    Terminal characters are taller than they are wide, so the height is
    corrected using a 0.45 multiplier to preserve the apparent aspect ratio.
    """
    term_width = shutil.get_terminal_size((100, 40)).columns

    if max_width is None:
        max_width = min(term_width, DEFAULT_MAX_WIDTH)

    if max_width <= 0:
        raise ValueError("Width must be greater than 0.")

    height, width = image.shape[:2]

    if width == 0:
        raise ValueError("Image has an invalid width.")

    aspect_ratio = height / width

    new_width = max_width
    new_height = int(aspect_ratio * new_width * 0.45)

    return cv2.resize(
        image,
        (new_width, max(1, new_height)),
        interpolation=cv2.INTER_AREA
    )


def isolate_foreground(image):
    """
    Attempt to isolate the foreground using OpenCV GrabCut.

    The outer 8% of the image is treated as likely background.
    """
    height, width = image.shape[:2]

    mask = np.zeros((height, width), np.uint8)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    margin_x = max(1, int(width * 0.08))
    margin_y = max(1, int(height * 0.08))

    rect_width = width - (2 * margin_x)
    rect_height = height - (2 * margin_y)

    # GrabCut requires a valid rectangle.
    if rect_width <= 0 or rect_height <= 0:
        return image

    rect = (
        margin_x,
        margin_y,
        rect_width,
        rect_height
    )

    cv2.grabCut(
        image,
        mask,
        rect,
        bg_model,
        fg_model,
        2,
        cv2.GC_INIT_WITH_RECT
    )

    foreground_mask = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
        255,
        0
    ).astype("uint8")

    foreground = cv2.bitwise_and(
        image,
        image,
        mask=foreground_mask
    )

    white_background = np.full_like(image, 255)

    result = np.where(
        foreground_mask[:, :, None] == 255,
        foreground,
        white_background
    )

    return result


def prepare_image(path, width=None, isolate=True):
    """
    Load and prepare an image for ASCII rendering.

    This centralizes the shared loading, resizing, and foreground isolation
    used by both terminal/text output and image output.
    """
    image = cv2.imread(str(path))

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {path}"
        )

    image = resize_for_terminal(
        image,
        width
    )

    if isolate:
        try:
            image = isolate_foreground(image)

        except cv2.error:
            # Foreground isolation can fail on unusual or tiny
            # images. In that case, keep the original image.
            print(
                "Warning: foreground isolation failed. "
                "Continuing without isolation.",
                file=sys.stderr
            )

    return image


# ---------------------------------------------------------------------------
# ASCII Conversion
# ---------------------------------------------------------------------------

def pixel_to_ascii(gray_pixel, chars=ASCII_CHARS):
    """Map a grayscale pixel value from 0-255 to an ASCII character."""
    index = int(
        gray_pixel / 255 * (len(chars) - 1)
    )

    return chars[index]


def image_to_ascii(
    image,
    color=False,
    chars=ASCII_CHARS,
    equalize=True,
    invert=False
):
    """
    Convert an OpenCV image into ASCII artwork.

    color:
        Apply ANSI true-color escape sequences.

    chars:
        Characters used for brightness mapping.

    equalize:
        Apply histogram equalization to improve contrast.

    invert:
        Reverse the brightness mapping.
    """
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    if equalize:
        gray = cv2.equalizeHist(gray)

    if invert:
        gray = 255 - gray

    lines = []

    for y in range(image.shape[0]):
        line = []

        for x in range(image.shape[1]):
            gray_pixel = gray[y, x]

            char = pixel_to_ascii(
                gray_pixel,
                chars
            )

            if color:
                b, g, r = image[y, x]

                line.append(
                    f"{rgb_to_ansi(r, g, b)}{char}{RESET}"
                )
            else:
                line.append(char)

        lines.append("".join(line))

    return "\n".join(lines)


def generate_ascii(
    path,
    width=None,
    isolate=True,
    color=False,
    chars=ASCII_CHARS,
    equalize=True,
    invert=False
):
    """
    Load an image, resize it, optionally isolate its foreground,
    and convert it to ASCII artwork.
    """
    image = prepare_image(
        path=path,
        width=width,
        isolate=isolate
    )

    return image_to_ascii(
        image,
        color=color,
        chars=chars,
        equalize=equalize,
        invert=invert
    )


# ---------------------------------------------------------------------------
# ASCII Image Rendering
# ---------------------------------------------------------------------------

def get_monospace_font(size=IMAGE_FONT_SIZE):
    """
    Load a monospace font for rendered ASCII images.

    Prefer common macOS monospace fonts and fall back to Pillow's
    default font if none are available.
    """
    font_paths = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/Menlo.ttc",
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(
                    font_path,
                    size=size
                )
            except OSError:
                pass

    return ImageFont.load_default()


def image_to_ascii_image(
    image,
    color=False,
    chars=ASCII_CHARS,
    equalize=True,
    invert=False
):
    """
    Render ASCII artwork as a Pillow image.

    If color is False, all ASCII characters are rendered in black.

    If color is True, each ASCII character is rendered using the RGB
    color of its corresponding source-image pixel.
    """
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    if equalize:
        gray = cv2.equalizeHist(gray)

    if invert:
        gray = 255 - gray

    font = get_monospace_font()

    # Measure one representative monospace character.
    measurement_image = Image.new(
        "RGB",
        (100, 100),
        IMAGE_BACKGROUND
    )

    measurement_draw = ImageDraw.Draw(
        measurement_image
    )

    bbox = measurement_draw.textbbox(
        (0, 0),
        "M",
        font=font
    )

    char_width = max(1, int(bbox[2] - bbox[0]))
    char_height = max(1, int(bbox[3] - bbox[1]))

    # Add a little vertical spacing so rows do not collide.
    line_height = char_height + 2

    ascii_width = image.shape[1]
    ascii_height = image.shape[0]

    canvas_width = (
        ascii_width * char_width
        + IMAGE_PADDING * 2
    )

    canvas_height = (
        ascii_height * line_height
        + IMAGE_PADDING * 2
    )

    canvas = Image.new(
        "RGB",
        (canvas_width, canvas_height),
        IMAGE_BACKGROUND
    )

    draw = ImageDraw.Draw(canvas)

    for y in range(ascii_height):
        for x in range(ascii_width):
            gray_pixel = gray[y, x]

            char = pixel_to_ascii(
                gray_pixel,
                chars
            )

            # There's nothing useful to draw for a literal space.
            if char == " ":
                continue

            if color:
                b, g, r = image[y, x]

                fill = (
                    int(r),
                    int(g),
                    int(b)
                )
            else:
                fill = IMAGE_FOREGROUND

            x_position = (
                IMAGE_PADDING
                + x * char_width
            )

            y_position = (
                IMAGE_PADDING
                + y * line_height
            )

            draw.text(
                (x_position, y_position),
                char,
                font=font,
                fill=fill
            )

    return canvas


def generate_ascii_image(
    path,
    width=None,
    isolate=True,
    color=False,
    chars=ASCII_CHARS,
    equalize=True,
    invert=False
):
    """
    Load an image and render its ASCII representation as an image.
    """
    image = prepare_image(
        path=path,
        width=width,
        isolate=isolate
    )

    return image_to_ascii_image(
        image,
        color=color,
        chars=chars,
        equalize=equalize,
        invert=invert
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def copy_text_to_clipboard(text):
    """Copy plain ASCII artwork to the system clipboard."""
    try:
        import pyperclip

    except ImportError:
        print(
            "Error: text clipboard support requires pyperclip.",
            file=sys.stderr
        )
        print(
            "Install it with:",
            file=sys.stderr
        )
        print(
            "  pip install pyperclip",
            file=sys.stderr
        )

        return False

    try:
        pyperclip.copy(text)
        return True

    except pyperclip.PyperclipException as exc:
        print(
            f"Error: could not access the clipboard: {exc}",
            file=sys.stderr
        )

        return False


def copy_image_to_clipboard(image):
    """
    Copy a Pillow image to the macOS clipboard.

    The image is temporarily saved as PNG and placed onto the clipboard
    through AppleScript.
    """
    if sys.platform != "darwin":
        print(
            "Error: image clipboard support currently requires macOS.",
            file=sys.stderr
        )
        return False

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

        image.save(
            temp_path,
            format="PNG"
        )

        apple_script = f'''
        set imageFile to POSIX file "{temp_path}"
        set imageData to read imageFile as «class PNGf»
        set the clipboard to imageData
        '''

        result = subprocess.run(
            [
                "osascript",
                "-e",
                apple_script
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(
                "Error: could not copy ASCII image "
                "to the clipboard.",
                file=sys.stderr
            )

            if result.stderr:
                print(
                    result.stderr.strip(),
                    file=sys.stderr
                )

            return False

        return True

    except OSError as exc:
        print(
            f"Error: could not copy image to clipboard: {exc}",
            file=sys.stderr
        )

        return False

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )


def save_to_file(text, output_path):
    """Save ASCII artwork as a UTF-8 text file."""
    path = Path(output_path)

    # Automatically add .txt if the user didn't specify an extension.
    if not path.suffix:
        path = path.with_suffix(".txt")

    path.write_text(
        text,
        encoding="utf-8"
    )

    return path


# ---------------------------------------------------------------------------
# Information
# ---------------------------------------------------------------------------

def display_info(
    source,
    art,
    color,
    isolate,
    chars,
    equalize,
    invert
):
    """Display information about the generated artwork."""
    lines = art.splitlines()

    height = len(lines)

    if lines:
        width = max(len(line) for line in lines)
    else:
        width = 0

    print()
    print("pyCasso output information")
    print("--------------------------")
    print(f"Source:       {source}")
    print(f"Width:        {width} characters")
    print(f"Height:       {height} lines")
    print(f"Color:        {'yes' if color else 'no'}")
    print(f"Isolation:    {'yes' if isolate else 'no'}")
    print(f"Equalization: {'yes' if equalize else 'no'}")
    print(f"Inverted:     {'yes' if invert else 'no'}")
    print(f"Characters:   {repr(chars)}")


# ---------------------------------------------------------------------------
# Uppercase Heading Formatter, Column Width Formatter
# ---------------------------------------------------------------------------

class UppercaseHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog):
        super().__init__(
            prog,
            max_help_position=48,
            width=120
        )

    def start_section(self, heading):
        super().start_section(heading.upper())


# ---------------------------------------------------------------------------
# Command-Line Interface
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="pycasso",
        usage=argparse.SUPPRESS,
        description=(
            "pyCasso - Terminal ASCII Art Generator\n\n"
            "Convert images into ASCII artwork for display "
            "in your terminal."
        ),
        epilog=" ",
        formatter_class=UppercaseHelpFormatter
    )

    # ------------------------------------------------------------------
    # Positional arguments
    # ------------------------------------------------------------------

    parser.add_argument(
        "image",
        help="path to the source image"
    )

    parser.add_argument(
        "width",
        nargs="?",
        type=int,
        help=(
            "maximum output width in characters "
            "(defaults to terminal width, up to 120)"
        )
    )

    # ------------------------------------------------------------------
    # Rendering options
    # ------------------------------------------------------------------

    rendering = parser.add_argument_group(
        "rendering options"
    )

    rendering.add_argument(
        "-c",
        "--color",
        action="store_true",
        help="render using source image colors"
    )

    rendering.add_argument(
        "--no-isolate",
        action="store_true",
        help="disable automatic foreground isolation"
    )

    rendering.add_argument(
        "--chars",
        default=ASCII_CHARS,
        metavar="CHARACTERS",
        help=(
            "characters used for brightness mapping "
            "(default: %(default)r)"
        )
    )

    rendering.add_argument(
        "--invert",
        action="store_true",
        help="invert the ASCII brightness mapping"
    )

    rendering.add_argument(
        "--no-equalize",
        action="store_true",
        help="disable histogram equalization"
    )

    # ------------------------------------------------------------------
    # Output options
    # ------------------------------------------------------------------

    output = parser.add_argument_group(
        "output options"
    )

    output.add_argument(
        "--copy-text",
        action="store_true",
        help="copy plain ASCII text to the clipboard"
    )

    output.add_argument(
        "--copy",
        action="store_true",
        help="copy rendered ASCII artwork as an image"
    )

    output.add_argument(
        "-o",
        "--output",
        "--print",
        dest="output",
        nargs="?",
        const=DEFAULT_OUTPUT_FILE,
        metavar="FILE",
        help=(
            "save plain ASCII artwork to FILE "
            f"(default: {DEFAULT_OUTPUT_FILE})"
        )
    )

    output.add_argument(
        "--info",
        action="store_true",
        help="display information about the generated artwork"
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Validate arguments
    # ------------------------------------------------------------------

    if args.width is not None and args.width <= 0:
        parser.error(
            "width must be greater than 0"
        )

    if len(args.chars) < 2:
        parser.error(
            "--chars must contain at least two characters"
        )

    image_path = Path(args.image)

    if not image_path.exists():
        parser.error(
            f"image does not exist: {image_path}"
        )

    if not image_path.is_file():
        parser.error(
            f"image path is not a file: {image_path}"
        )

    # ------------------------------------------------------------------
    # Generate artwork
    # ------------------------------------------------------------------

    try:
        terminal_art = generate_ascii(
            path=image_path,
            width=args.width,
            isolate=not args.no_isolate,
            color=args.color,
            chars=args.chars,
            equalize=not args.no_equalize,
            invert=args.invert
        )

        # Always display the artwork.
        print(terminal_art)

        # --------------------------------------------------------------
        # Plain version
        # --------------------------------------------------------------
        #
        # --copy-text and --output must ALWAYS use plain ASCII.
        #
        # Even if --color is active, ANSI escape sequences must never
        # enter the text clipboard or text output file.

        plain_art = None

        if args.copy_text or args.output:
            plain_art = generate_ascii(
                path=image_path,
                width=args.width,
                isolate=not args.no_isolate,
                color=False,
                chars=args.chars,
                equalize=not args.no_equalize,
                invert=args.invert
            )

        # --------------------------------------------------------------
        # Text Clipboard
        # --------------------------------------------------------------

        if args.copy_text:
            if copy_text_to_clipboard(plain_art):
                print()
                print(
                    "Copied ASCII text to clipboard. "
                    "For best results, paste in monospace font."
                )

        # --------------------------------------------------------------
        # Image Clipboard
        # --------------------------------------------------------------
        #
        # Unlike --copy-text, --copy respects --color:
        #
        #   --copy
        #       black-and-white ASCII image
        #
        #   --color --copy
        #       colored ASCII image

        if args.copy:
            ascii_image = generate_ascii_image(
                path=image_path,
                width=args.width,
                isolate=not args.no_isolate,
                color=args.color,
                chars=args.chars,
                equalize=not args.no_equalize,
                invert=args.invert
            )

            if copy_image_to_clipboard(ascii_image):
                print()
                print(
                    "Copied ASCII artwork image to clipboard."
                )

        # --------------------------------------------------------------
        # File output
        # --------------------------------------------------------------

        if args.output:
            output_path = save_to_file(
                plain_art,
                args.output
            )

            print()
            print(
                f"Saved ASCII artwork to: {output_path}"
            )

        # --------------------------------------------------------------
        # Information
        # --------------------------------------------------------------

        if args.info:
            # Use the plain version if available so ANSI codes don't
            # distort the reported character width.

            if plain_art is None:
                info_art = generate_ascii(
                    path=image_path,
                    width=args.width,
                    isolate=not args.no_isolate,
                    color=False,
                    chars=args.chars,
                    equalize=not args.no_equalize,
                    invert=args.invert
                )
            else:
                info_art = plain_art

            display_info(
                source=image_path,
                art=info_art,
                color=args.color,
                isolate=not args.no_isolate,
                chars=args.chars,
                equalize=not args.no_equalize,
                invert=args.invert
            )

    except FileNotFoundError as exc:
        parser.error(str(exc))

    except PermissionError as exc:
        print(
            f"Error: permission denied: {exc}",
            file=sys.stderr
        )
        sys.exit(1)

    except OSError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr
        )
        sys.exit(1)

    except KeyboardInterrupt:
        print(
            "\nGeneration cancelled.",
            file=sys.stderr
        )
        sys.exit(130)


if __name__ == "__main__":
    main()