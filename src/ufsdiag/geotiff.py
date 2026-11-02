"""Lecture minimale de GeoTIFF (strips, LZW, float32) + projection Lambert-93 (EPSG:2154).
Stdlib uniquement. Suffisant pour échantillonner les rasters officiels DataGrandLyon.
"""
import math
import struct
import zlib


def _lzw_decode(data):
    """Décodeur LZW variante TIFF (clear=256, eoi=257, codes 9-12 bits)."""
    out = bytearray()
    table = None
    bitpos = 0
    prev = None

    def reset():
        return {i: bytes([i]) for i in range(256)}

    table = reset()
    next_code = 258
    code_size = 9
    result = bytearray()
    while True:
        if bitpos + code_size > len(data) * 8:
            break
        byte_i = bitpos // 8
        bit_i = bitpos % 8
        chunk = int.from_bytes(data[byte_i:byte_i + 3].ljust(3, b"\0"), "little")
        code = (chunk >> bit_i) & ((1 << code_size) - 1)
        bitpos += code_size
        if code == 256:
            table = reset()
            next_code = 258
            code_size = 9
            prev = None
            continue
        if code == 257:
            break
        if prev is None:
            entry = table[code]
            result += entry
            prev = entry
            continue
        if code in table:
            entry = table[code]
        elif code == next_code:
            entry = prev + prev[:1]
        else:
            raise ValueError(f"code LZW invalide {code}")
        result += entry
        table[next_code] = prev + entry[:1]
        next_code += 1
        prev = entry
        if next_code == (1 << code_size) - 1 and code_size < 12:
            code_size += 1
    return bytes(result)


class GeoTiffFloat:
    def __init__(self, path):
        raw = open(path, "rb").read()
        endian = "<" if raw[:2] == b"II" else ">"
        self.endian = endian
        self.raw = raw
        ifd = struct.unpack(endian + "I", raw[4:8])[0]
        n = struct.unpack(endian + "H", raw[ifd:ifd + 2])[0]
        tags = {}
        for i in range(n):
            off = ifd + 2 + i * 12
            tag, typ, cnt = struct.unpack(endian + "HHI", raw[off:off + 8])
            val = raw[off + 8:off + 12]
            tags[tag] = (typ, cnt, val)
        self.width = self._scalar(tags, 256)
        self.height = self._scalar(tags, 257)
        self.bits = self._scalar(tags, 258, 32)
        self.compression = self._scalar(tags, 259, 1)
        self.samples = self._scalar(tags, 277, 1)
        self.tiled = 322 in tags
        if self.tiled:
            self.tile_w = self._scalar(tags, 322)
            self.tile_h = self._scalar(tags, 323)
            self.tile_offsets = self._array(tags, 324)
            self.tile_counts = self._array(tags, 325)
            self.tiles_across = (self.width + self.tile_w - 1) // self.tile_w
        else:
            self.tile_offsets = self._array(tags, 273)
            self.tile_counts = self._array(tags, 279)
            self.tile_w = self.width
            self.tile_h = self.height // len(self.tile_offsets) + 1
            self.tiles_across = 1
        scale = self._doubles(tags, 34264) or (1.0, 1.0, 0.0)
        tie = self._doubles(tags, 33922) or (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.pixel_w = scale[0]
        self.pixel_h = -abs(scale[1])
        self.origin_x = tie[3]
        self.origin_y = tie[4]
        self._tile_cache = {}

    def _scalar(self, tags, tag, default=None):
        if tag not in tags:
            return default
        typ, cnt, val = tags[tag]
        if typ in (3,):  # short
            return struct.unpack(self.endian + "H", val[:2])[0]
        return struct.unpack(self.endian + "I", val[:4])[0]

    def _array(self, tags, tag):
        typ, cnt, val = tags[tag]
        fmt = {3: "H", 4: "I"}.get(typ, "I")
        if cnt * struct.calcsize(fmt) <= 4:
            data = val[:cnt * struct.calcsize(fmt)]
        else:
            off = struct.unpack(self.endian + "I", val)[0]
            data = self.raw[off:off + cnt * struct.calcsize(fmt)]
        return list(struct.unpack(self.endian + fmt * cnt, data))

    def _doubles(self, tags, tag):
        if tag not in tags:
            return None
        typ, cnt, val = tags[tag]
        off = struct.unpack(self.endian + "I", val)[0] if cnt * 8 > 4 else None
        data = val[:cnt * 8] if off is None else self.raw[off:off + cnt * 8]
        return struct.unpack(self.endian + "d" * cnt, data)

    def _decode_tile(self, ti):
        if ti in self._tile_cache:
            return self._tile_cache[ti]
        off, cnt = self.tile_offsets[ti], self.tile_counts[ti]
        chunk = self.raw[off:off + cnt]
        if self.compression == 5:
            chunk = _lzw_decode(chunk)
        elif self.compression == 8:
            chunk = zlib.decompress(chunk)
        elif self.compression == 32773:
            chunk = _packbits_decode(chunk)
        floats = struct.unpack("<" + "f" * (len(chunk) // 4), chunk[:len(chunk) // 4 * 4])
        self._tile_cache[ti] = floats
        return floats

    def sample(self, x, y, nodata=-9999.0):
        """x,y en coordonnées monde (même CRS que le tiepoint)."""
        col = int((x - self.origin_x) / self.pixel_w)
        row = int((self.origin_y - y) / abs(self.pixel_h))
        if col < 0 or row < 0 or col >= self.width or row >= self.height:
            return None
        tc, tr = col // self.tile_w, row // self.tile_h
        ti = tr * self.tiles_across + tc
        if ti >= len(self.tile_offsets):
            return None
        floats = self._decode_tile(ti)
        lc, lr = col % self.tile_w, row % self.tile_h
        i = lr * self.tile_w + lc
        if i >= len(floats):
            return None
        v = floats[i]
        return None if v == nodata else v


def _packbits_decode(data):
    out = bytearray()
    i = 0
    while i < len(data):
        n = data[i]
        i += 1
        if n < 128:
            out += data[i:i + n + 1]
            i += n + 1
        elif n > 128:
            out += data[i:i + 1] * (257 - n)
            i += 1
    return bytes(out)


# --- Lambert-93 (EPSG:2154) : constantes officielles IGN (document CNIG/IGN "Représentations planes", p.32) ---
_N93 = 0.7256077650
_C93 = 11754255.426
_XS93 = 700000.0
_YS93 = 12655612.050
_LON0_93 = math.radians(3.0)
_E93 = 0.08181919112


def wgs84_to_l93(lon, lat):
    """WGS84 (≈RGF93) -> EPSG:2154, formule IGN (latitude isométrique)."""
    phi = math.radians(lat)
    lam = math.radians(lon)
    eps = 0.5 * math.log((1 + math.sin(phi)) / (1 - math.sin(phi))) \
        - (_E93 / 2) * math.log((1 + _E93 * math.sin(phi)) / (1 - _E93 * math.sin(phi)))
    R = _C93 * math.exp(-_N93 * eps)
    gamma = _N93 * (lam - _LON0_93)
    x = _XS93 + R * math.sin(gamma)
    y = _YS93 - R * math.cos(gamma)
    return x, y
