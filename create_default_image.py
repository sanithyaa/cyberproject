"""
Run once to create a default candidate placeholder image.
Requires Pillow: pip install Pillow
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (200, 200), color=(30, 40, 60))
    draw = ImageDraw.Draw(img)
    # Draw a simple person silhouette
    draw.ellipse([70, 30, 130, 90], fill=(100, 130, 180))   # head
    draw.rectangle([60, 95, 140, 170], fill=(100, 130, 180)) # body
    draw.text((50, 175), "Candidate", fill=(180, 200, 220))
    out = os.path.join('static', 'images', 'default_candidate.png')
    img.save(out)
    # Also copy to uploads
    img.save(os.path.join('static', 'uploads', 'default_candidate.png'))
    print(f'Created {out}')
except ImportError:
    # Fallback: create a minimal 1x1 PNG
    import struct, zlib
    def create_png(w, h, r, g, b):
        def chunk(name, data):
            c = zlib.crc32(name + data) & 0xffffffff
            return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        raw = b''.join(b'\x00' + bytes([r, g, b] * w) for _ in range(h))
        idat = zlib.compress(raw)
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
    data = create_png(100, 100, 30, 40, 60)
    for path in ['static/images/default_candidate.png', 'static/uploads/default_candidate.png']:
        with open(path, 'wb') as f:
            f.write(data)
    print('Created minimal default_candidate.png (install Pillow for a better image)')
