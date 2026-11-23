#!/usr/bin/env python3
"""Copy the finished front-page image to the output directory.

entry.png sits next to this file. Before anything is copied, the
bytes are checked as a complete PNG within the competition limits:
the 8-byte signature, a 13-byte IHDR first chunk no larger than
1024 on either side, a total size of at most 1 MiB, a correct CRC
on every chunk, and an IEND with nothing after it. The copy is then
read back and compared, so what lands in the output directory is
exactly what was checked. Standard library only.
"""

import os
import struct
import sys
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
BYTE_LIMIT = 1_048_576
SIDE_LIMIT = 1024


def refuse(reason):
    sys.stderr.write("main.py: entry.png rejected: %s\n" % reason)
    return 1


def validate(blob):
    """None if blob is a whole in-limits PNG, else the problem."""
    if len(blob) > BYTE_LIMIT:
        return "size %d exceeds the %d byte limit" % (len(blob), BYTE_LIMIT)
    if blob[:8] != SIGNATURE:
        return "PNG signature missing"

    offset = 8
    have_ihdr = False
    have_iend = False
    while offset < len(blob):
        if offset + 8 > len(blob):
            return "chunk header cut off at byte %d" % offset
        (chunk_len,) = struct.unpack(">I", blob[offset:offset + 4])
        chunk_type = blob[offset + 4:offset + 8]
        chunk_end = offset + 12 + chunk_len
        if chunk_end > len(blob):
            return "chunk %r runs past the end of the file" % chunk_type
        body = blob[offset + 8:offset + 8 + chunk_len]
        (crc_seen,) = struct.unpack(
            ">I", blob[offset + 8 + chunk_len:chunk_end])
        crc_calc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
        if crc_calc != crc_seen:
            return "bad CRC on chunk %r" % chunk_type
        if not have_ihdr:
            if chunk_type != b"IHDR" or chunk_len != 13:
                return "first chunk must be a 13-byte IHDR"
            w, h = struct.unpack(">II", body[:8])
            if w == 0 or h == 0:
                return "zero-sized image"
            if w > SIDE_LIMIT or h > SIDE_LIMIT:
                return "image is %dx%d, limit is %d per side" % (
                    w, h, SIDE_LIMIT)
            have_ihdr = True
        offset = chunk_end
        if chunk_type == b"IEND":
            have_iend = True
            break

    if not have_ihdr:
        return "no IHDR found"
    if not have_iend:
        return "no IEND found"
    if offset != len(blob):
        return "extra bytes follow IEND"
    return None


def run():
    base = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(base, "entry.png")
    try:
        with open(src_path, "rb") as fh:
            blob = fh.read()
    except OSError as err:
        return refuse("cannot open %s (%s)" % (src_path, err))

    problem = validate(blob)
    if problem is not None:
        return refuse(problem)

    dest_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, "entry.png")
        with open(dest_path, "wb") as fh:
            fh.write(blob)
        with open(dest_path, "rb") as fh:
            landed = fh.read()
    except OSError as err:
        return refuse("cannot deliver to %s (%s)" % (dest_dir, err))
    if landed != blob:
        return refuse("delivered bytes differ from the checked bytes")
    return 0


if __name__ == "__main__":
    sys.exit(run())
