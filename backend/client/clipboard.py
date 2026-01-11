import subprocess


def read_clipboard_text() -> str:
    """macOS: read clipboard via pbpaste."""
    p = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return p.stdout


def write_clipboard_text(text: str) -> None:
    """macOS: write clipboard via pbcopy."""
    subprocess.run(["pbcopy"], input=text, text=True, check=True)