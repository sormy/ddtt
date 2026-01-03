# Divine Divinity Text Translator

A tool to extract and modify text from Divine Divinity game data files with text
(`mono.cmp` - monologues, `itemgen.cmp` - item prefixes/suffixes,
`treasure.cmp` - item names).

## Usage

```bash
# Extract text from binary file
./ddtt.py decode input.cmp output.txt

# Apply modified text back to binary
./ddtt.py encode input.txt output.cmp

# Use different character encoding (default: cp1252)
./ddtt.py --charset cp1251 decode input.cmp output.txt
```

## How It Works

The tool scans binary data for length-prefixed strings:

- 4-byte little-endian length (includes null terminator)
- Variable-length text (CP1252 by default)
- Null terminator

**String detection heuristics:**

- Length between 4-2000 bytes
- At least 80% printable characters
- Valid encoding in target charset

**Important for translators:**

The tool may misinterpret binary data as text. Watch for strings that break
common patterns:

- Lowercase text where everything else is capitalized
- Context-inappropriate names (e.g., "orc" appearing as an item name)
- Nonsensical character combinations
- Strings that don't fit the surrounding content pattern

When in doubt, leave suspicious strings unchanged or verify against the game.

**Text format:**

The exported/imported text file is always UTF-8 encoded, regardless of the
charset used in the binary file. The tool will error if characters cannot be
converted between the binary charset and UTF-8. If this occurs, either adjust
the `--charset` parameter or modify the problematic text.

- Strings: `"escaped text\n"`
- Binary data: `# FF 00 A1 B2`
- Comments: `// ignored`

The algorithm is primitive but effective for game translation workflows. The
tool is self-contained with no external dependencies beyond Python 3 standard
library.

## License

MIT License - see LICENSE file for details.

This tool is for educational and modding purposes.
