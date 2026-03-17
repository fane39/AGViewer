# AGViewer - AmigaGuide Viewer for Python

AGViewer is a robust, lightweight AmigaGuide (`.guide`) file viewer implemented in Python using Tkinter. It aims to provide an authentic Amiga-like reading experience on modern operating systems, supporting complex node navigation, text formatting, and interactive commands.

## Features

- **Authentic Navigation:**
  - **Contents & Index:** Quickly jump to the main table of contents or the document index.
  - **Retrace:** Full navigation history allowing you to backtrack through visited nodes (even across different files).
  - **Browse < / >:** Sequential navigation through nodes, just like the original Amiga viewer.
  - **Cross-File Linking:** Seamlessly follow links to other `.guide` files with automatic path resolution.

- **Rich Text Rendering:**
  - Supports standard AmigaGuide formatting: **Bold**, *Italic*, and <u>Underline</u>.
  - Interactive **Button-style links** with hover effects and 3D relief.
  - Text alignment support (`jleft`, `jcenter`, `jright`).
  - Color support for foreground and background text.
  - Correct handling of escaped characters (`\@`, `\\`).

- **Utility Tools:**
  - **Integrated Search (Ctrl+F):** Find text within the current node with visual highlighting.
  - **Raw Mode:** Toggle between the parsed view and the raw AmigaGuide source code.
  - **Copy to Clipboard:** Easily copy text from the viewer.
  - **System Command Support:** Executes Amiga `system` commands (with user confirmation).

- **Performance & Compatibility:**
  - Handles large files (tested with guides over 4,700 lines) with smooth scrolling.
  - Automatic encoding detection (defaults to `ISO-8859-1` for legacy Amiga compatibility).
  - Modern, clean UI with a classic monospaced font aesthetic.

## Requirements

- **Python 3.x**
- **Tkinter** (usually included with standard Python installations)

## Installation & Usage

1. **Clone or Download** the repository.
2. **Run the application:**
   ```bash
   python AGViewer.py
   ```
3. **Open a Guide:** Click the **Open** button and select any `.guide` file.

## Shortcuts

- `Ctrl + F`: Open the Find dialog.
- `Left Click`: Interact with links/buttons.

## License

This project is open-source. Feel free to modify and adapt it for your own needs.

---
*Created to keep the spirit of Amiga computing alive on modern systems.*
