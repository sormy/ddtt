#!/usr/bin/env python3

# flake8: noqa: E501
# ruff: noqa: E401

import argparse
import struct


def is_valid_string(byte):
    if 0x20 <= byte <= 0x7E:
        return True
    if byte in (0x09, 0x0A, 0x0D):
        return True
    if 0x80 <= byte <= 0xFF:
        return True
    return False


def try_read_string(data, offset, charset):
    if offset + 4 > len(data):
        return None, 0

    length = struct.unpack("<I", data[offset : offset + 4])[0]

    if not (4 <= length <= 2000):
        return None, 0

    str_offset = offset + 4
    if str_offset + length > len(data):
        return None, 0

    if data[str_offset + length - 1] != 0:
        return None, 0

    text_bytes = data[str_offset : str_offset + length - 1]

    for byte in text_bytes:
        if not is_valid_string(byte):
            return None, 0

    printable_count = sum(
        1 for b in text_bytes if 0x20 <= b <= 0x7E or b in (0x09, 0x0A, 0x0D)
    )
    if len(text_bytes) > 0 and printable_count / len(text_bytes) < 0.80:
        return None, 0

    try:
        text = text_bytes.decode(charset)
        return text, 4 + length
    except (UnicodeDecodeError, ValueError):
        return None, 0


def encode_to_text(binary_data, charset):
    lines = []
    offset = 0

    while offset < len(binary_data):
        text, consumed = try_read_string(binary_data, offset, charset)

        if text is not None:
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            escaped = (
                escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            )
            lines.append(f'"{escaped}"')
            offset += consumed
        else:
            chunk_bytes = []

            while offset < len(binary_data):
                text, consumed = try_read_string(binary_data, offset, charset)
                if text is not None:
                    break

                chunk_bytes.append(binary_data[offset])
                offset += 1

                if len(chunk_bytes) >= 16:
                    break

            hex_str = " ".join(f"{b:02X}" for b in chunk_bytes)
            lines.append(f"# {hex_str}")

    return lines


def decode_from_text(lines, charset):
    binary_parts = []

    for line_num, line in enumerate(lines, 1):
        line = line.rstrip("\n\r")

        if not line or line.startswith("//"):
            continue

        if line.startswith("# "):
            hex_part = line[2:].strip()
            if not hex_part:
                continue

            hex_bytes = hex_part.split()
            try:
                for hex_byte in hex_bytes:
                    binary_parts.append(bytes.fromhex(hex_byte))
            except ValueError as e:
                raise ValueError(f"Line {line_num}: Invalid hex data: {e}")

        elif line.startswith('"') and line.endswith('"'):
            escaped_text = line[1:-1]

            text = (
                escaped_text.replace("\\n", "\n")
                .replace("\\r", "\r")
                .replace("\\t", "\t")
            )
            text = text.replace('\\"', '"').replace("\\\\", "\\")

            try:
                text_bytes = text.encode(charset)
            except UnicodeEncodeError as e:
                raise ValueError(f"Line {line_num}: Cannot encode to {charset}: {e}")

            length = len(text_bytes) + 1
            length_bytes = struct.pack("<I", length)

            binary_parts.append(length_bytes)
            binary_parts.append(text_bytes)
            binary_parts.append(b"\x00")

        else:
            raise ValueError(
                f"Line {line_num}: Invalid format (must start with '# ' or '\"')"
            )

    return b"".join(binary_parts)


def decode_file(input_path, output_path, charset):
    with open(input_path, "rb") as f:
        binary_data = f.read()

    lines = encode_to_text(binary_data, charset)

    with open(output_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Decoded {len(binary_data)} bytes to {len(lines)} lines")


def encode_file(input_path, output_path, charset):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    binary_data = decode_from_text(lines, charset)

    with open(output_path, "wb") as f:
        f.write(binary_data)

    print(f"Encoded {len(lines)} lines to {len(binary_data)} bytes")


def main():
    parser = argparse.ArgumentParser(description="Divine Divinity Text Translator")
    parser.add_argument(
        "--charset",
        default="cp1252",
        help="Character encoding to use (default: cp1252)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    decode_parser = subparsers.add_parser("decode", help="Convert binary to text")
    decode_parser.add_argument("input", help="Input .cmp file")
    decode_parser.add_argument("output", help="Output .txt file")

    encode_parser = subparsers.add_parser("encode", help="Convert text to binary")
    encode_parser.add_argument("input", help="Input .txt file")
    encode_parser.add_argument("output", help="Output .cmp file")

    args = parser.parse_args()

    if args.command == "decode":
        decode_file(args.input, args.output, args.charset)
    elif args.command == "encode":
        encode_file(args.input, args.output, args.charset)


if __name__ == "__main__":
    main()
