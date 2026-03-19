# AGViewer - AmigaGuide Viewer for Python

AGViewer is a robust, lightweight AmigaGuide (`.guide`) file viewer implemented in Python using Tkinter. It provides an authentic Amiga-like experience on modern operating systems, supporting complex node navigation, text formatting, and interactive images.

## Features

- **Authentic Navigation:**
  - **Contents & Index:** Quickly jump to the main table of contents or the document index.
  - **Retrace:** Full cross-file navigation history allowing you to backtrack through visited nodes.
  - **Browse < / >:** Sequential navigation through nodes, just like the original Amiga viewer.
  - **Cross-File Linking:** Seamlessly follow links between different `.guide` files.

- **IFF/ILBM Image Viewer:**
  - **Integrated Viewing:** Automatically opens `.iff`, `.lbm`, and `.ilbm` files in a specialized window.
  - **Hybrid Decoder:** Uses **Pillow** for modern compatibility with a custom **Amiga Bitplane Fallback** for legacy or non-standard IFF files.
  - **Smart Resolution:** Resolves image paths relative to the current guide, even without explicit file extensions.

- **Rich Text Rendering:**
  - Supports standard AmigaGuide formatting: **Bold**, *Italic*, and <u>Underline</u>.
  - Interactive **Button-style links** with hover effects and 3D relief.
  - Text alignment support (`jleft`, `jcenter`, `jright`).
  - Color support for foreground and background text.
  - Correct handling of escaped characters (`\@`, `\\`).

- **Wrapping Support:**
  - **Smartwrap:** Intelligently reflows text into paragraphs while preserving indentation and headers.
  - **Wordwrap:** Supports standard line wrapping and horizontal scrolling for pre-formatted text.

- **Utility Tools:**
  - **Integrated Search (Ctrl+F):** Find text within the current node with visual highlighting.
  - **Raw Mode:** Toggle between the parsed view and the raw AmigaGuide source code.
  - **Copy to Clipboard:** Easily copy text (formatted or selected) from the viewer.
  - **System Commands:** Support for `system`, `beep`, and `rx` command links.

## Requirements

- **Python 3.x**
- **Tkinter** (usually included with standard Python)
- **Pillow** (recommended for full IFF image support)
  ```bash
  pip install pillow
  ```

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
*Created to keep the spirit of Amiga computing alive on modern systems. Developed in collaboration with Gemini CLI and GitHub Copilot*
