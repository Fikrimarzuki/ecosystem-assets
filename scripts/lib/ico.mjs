// Multi-resolution ICO with PNG-compressed frames (supported by every current browser and by Windows Vista+).
export function buildIco(frames) { // frames: [{ size, png: Buffer }]
  const head = Buffer.alloc(6 + frames.length * 16);
  head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(frames.length, 4);
  let offset = head.length;
  frames.forEach(({ size, png }, i) => {
    const e = 6 + i * 16;
    head[e] = size >= 256 ? 0 : size; head[e + 1] = size >= 256 ? 0 : size;
    head.writeUInt16LE(1, e + 4); head.writeUInt16LE(32, e + 6);
    head.writeUInt32LE(png.length, e + 8); head.writeUInt32LE(offset, e + 12);
    offset += png.length;
  });
  return Buffer.concat([head, ...frames.map(f => f.png)]);
}

export function parseIco(buf) {
  if (buf.length < 6 || buf.readUInt16LE(0) !== 0 || buf.readUInt16LE(2) !== 1) throw new Error("Not an ICO file");
  const count = buf.readUInt16LE(4), frames = [];
  for (let i = 0; i < count; i++) {
    const e = 6 + i * 16, len = buf.readUInt32LE(e + 8), off = buf.readUInt32LE(e + 12);
    if (off + len > buf.length) throw new Error(`ICO frame ${i} runs past the end of the file`);
    frames.push({ width: buf[e] || 256, height: buf[e + 1] || 256, bpp: buf.readUInt16LE(e + 6), png: buf.subarray(off, off + len) });
  }
  return frames;
}
