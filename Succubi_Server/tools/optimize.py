"""Shrink the package without touching geometry: UVs are relative (texture_width / normalized_uvs),
so textures can be resized and palette-reduced safely."""
import glob, os, subprocess
from PIL import Image


def png(path, size=None, colors=256):
    im = Image.open(path)
    if size and im.size[0] > size:
        im = im.resize((size, size * im.size[1] // im.size[0]), Image.LANCZOS)
    has_alpha = im.mode in ('RGBA', 'LA', 'P') and im.convert('RGBA').getextrema()[3][0] < 255
    im = im.convert('RGBA' if has_alpha else 'RGB')
    q = im.quantize(colors, method=Image.Quantize.FASTOCTREE if has_alpha else Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.FLOYDSTEINBERG)
    q.save(path, optimize=True)


def ogg(path, quality=0):
    import imageio_ffmpeg
    tmp = path + '.tmp.ogg'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error', '-i', path, '-c:a', 'libvorbis', '-q:a', str(quality), tmp], check=True)
    os.replace(tmp, path)


def run(out, log):
    before = sum(os.path.getsize(f) for f in glob.glob(f'{out}/**/*', recursive=True) if os.path.isfile(f))
    rp = f'{out}/Succubi Server RP'
    for f in glob.glob(f'{rp}/textures/entity/kiosks/*.png'):
        png(f)                       # kiosks are big on screen: keep 1024, palette only
    for f in glob.glob(f'{rp}/textures/entity/food/*.png'):
        png(f, size=512)             # hand-held food: 512 is plenty
    for f in glob.glob(f'{out}/*/pack_icon.png'):
        png(f, size=256)
    ogg(f'{rp}/sounds/kiosk/tea_bgm_01.ogg', 0)   # 11:55 of background music, 160 -> ~64 kb/s
    after = sum(os.path.getsize(f) for f in glob.glob(f'{out}/**/*', recursive=True) if os.path.isfile(f))
    log(f'optimized {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB (unpacked)')
