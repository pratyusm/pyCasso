import cv2
import numpy as np
import shutil
import sys
from colorama import init

init()

ASCII_CHARS = " .:-=+*#%@"
RESET = "\033[0m"


def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def resize_for_terminal(image, max_width=None):
    term_width = shutil.get_terminal_size((100, 40)).columns

    if max_width is None:
        max_width = min(term_width, 120)

    height, width = image.shape[:2]
    aspect_ratio = height / width

    new_width = max_width
    new_height = int(aspect_ratio * new_width * 0.45)

    return cv2.resize(image, (new_width, max(1, new_height)))


def isolate_foreground(image):
    h, w = image.shape[:2]

    mask = np.zeros((h, w), np.uint8)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    margin_x = int(w * 0.08)
    margin_y = int(h * 0.08)

    rect = (
        margin_x,
        margin_y,
        w - 2 * margin_x,
        h - 2 * margin_y
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

    foreground = cv2.bitwise_and(image, image, mask=foreground_mask)
    white_bg = np.full_like(image, 255)

    result = np.where(
        foreground_mask[:, :, None] == 255,
        foreground,
        white_bg
    )

    return result


def pixel_to_ascii(gray_pixel):
    index = int(gray_pixel / 255 * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[index]


def image_to_ascii(image, color=False):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    lines = []

    for y in range(image.shape[0]):
        line = ""

        for x in range(image.shape[1]):
            gray_pixel = gray[y, x]
            char = pixel_to_ascii(gray_pixel)

            if color:
                b, g, r = image[y, x]
                line += f"{rgb_to_ansi(r, g, b)}{char}{RESET}"
            else:
                line += char

        lines.append(line)

    return "\n".join(lines)


def generate_ascii(path, width=None, isolate=True, color=False):
    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    # Resize first so GrabCut does not attempt to eat your entire afternoon
    image = resize_for_terminal(image, width)

    if isolate:
        image = isolate_foreground(image)

    return image_to_ascii(image, color=color)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ascii_art.py image.jpg [width] [--color] [--no-isolate]")
        print()
        print("Examples:")
        print("  python ascii_art.py lincoln.jpg")
        print("  python ascii_art.py lincoln.jpg 100")
        print("  python ascii_art.py lincoln.jpg 100 --color")
        print("  python ascii_art.py lincoln.jpg 80 --color --no-isolate")
        sys.exit(1)

    path = sys.argv[1]
    width = None
    color = False
    isolate = True

    for arg in sys.argv[2:]:
        if arg == "--color":
            color = True
        elif arg == "--no-isolate":
            isolate = False
        elif arg.isdigit():
            width = int(arg)
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    art = generate_ascii(
        path,
        width=width,
        isolate=isolate,
        color=color
    )

    print(art)


if __name__ == "__main__":
    main()