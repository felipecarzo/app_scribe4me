"""Gera logo minimalista para o Scribe4me.

Conceito: microfone line-art de onde sai a palavra 'Scribe'
em estilo handwriting, como se a voz virasse escrita.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont


# Paleta
BG_DARK = (20, 25, 60)
BG_MID = (30, 45, 100)
WHITE = (240, 242, 250)
WHITE_DIM = (180, 190, 220)
GREEN = (100, 210, 120)
GREEN_DIM = (100, 210, 120, 120)


def _get_handwriting_font(size: int):
    """Tenta carregar uma fonte manuscrita do Windows."""
    candidates = [
        "C:/Windows/Fonts/inkfree.ttf",      # Ink Free (Win10+)
        "C:/Windows/Fonts/segoesc.ttf",       # Segoe Script
        "C:/Windows/Fonts/LHANDW.TTF",        # Lucida Handwriting
        "C:/Windows/Fonts/comic.ttf",         # Comic Sans (fallback)
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_mic_solid(draw, cx, cy, s, fill_color, outline_color, line_w):
    """Desenha microfone com capsula preenchida — legivel em qualquer tamanho."""
    # Corpo do mic (capsula preenchida)
    cap_w = int(22 * s)
    cap_h = int(58 * s)
    cap_top = cy - int(44 * s)
    draw.rounded_rectangle(
        [cx - cap_w, cap_top, cx + cap_w, cap_top + cap_h],
        radius=cap_w,
        fill=fill_color,
        outline=outline_color,
        width=max(1, line_w // 2),
    )

    # Arco U (suporte)
    arc_w = int(32 * s)
    arc_top = cap_top + cap_h - int(16 * s)
    arc_h = int(28 * s)
    draw.arc(
        [cx - arc_w, arc_top, cx + arc_w, arc_top + arc_h * 2],
        start=0, end=180,
        fill=outline_color,
        width=line_w,
    )

    # Haste
    haste_top = arc_top + arc_h
    haste_bot = haste_top + int(18 * s)
    draw.line([cx, haste_top, cx, haste_bot], fill=outline_color, width=line_w)

    # Base
    base_hw = int(18 * s)
    draw.line([cx - base_hw, haste_bot, cx + base_hw, haste_bot],
              fill=outline_color, width=line_w)

    return cap_top, cap_top + cap_h // 2  # retorna topo e centro do mic


def _draw_flowing_curve(draw, x1, y1, x2, y2, color, width):
    """Desenha curva suave de x1,y1 a x2,y2 (bezier aproximada)."""
    steps = 30
    points = []
    # Control points para curva S suave
    cp1x = x1 + (x2 - x1) * 0.3
    cp1y = y1 - 15
    cp2x = x1 + (x2 - x1) * 0.7
    cp2y = y2 + 10
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3 * x1 + 3 * mt**2 * t * cp1x + 3 * mt * t**2 * cp2x + t**3 * x2
        y = mt**3 * y1 + 3 * mt**2 * t * cp1y + 3 * mt * t**2 * cp2y + t**3 * y2
        points.append((x, y))
    if len(points) >= 2:
        draw.line(points, fill=color, width=width, joint="curve")


def create_icon(size: int = 256) -> Image.Image:
    """Icone: microfone line-art com onda sutil."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    radius = size // 2 - 2
    s = size / 256

    # Fundo circular limpo
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=BG_DARK,
    )

    # Microfone centralizado (capsula preenchida para legibilidade)
    line_w = max(2, int(3.5 * s))
    mic_top, mic_mid = _draw_mic_solid(draw, cx, cy, s, WHITE_DIM, WHITE, line_w)

    # Ondas sonoras sutis (2 arcos finos saindo do mic)
    wave_w = max(1, int(2 * s))
    wave_cx = cx + int(32 * s)
    wave_cy = mic_mid

    for i, alpha in enumerate([180, 90]):
        r = int((14 + i * 14) * s)
        color = (100, 210, 120, alpha)
        draw.arc(
            [wave_cx - r, wave_cy - r, wave_cx + r, wave_cy + r],
            start=-40, end=40,
            fill=color,
            width=wave_w,
        )

    return img


def create_banner(width: int = 1280, height: int = 480) -> Image.Image:
    """Banner: microfone + curva fluida + 'Scribe4me' handwriting."""
    img = Image.new("RGBA", (width, height), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Gradiente horizontal sutil
    for x in range(width):
        t = x / width
        r = int(20 + 15 * t)
        g = int(25 + 25 * t)
        b = int(60 + 50 * t)
        draw.line([x, 0, x, height], fill=(r, g, b))

    s = height / 480

    # Microfone no lado esquerdo
    mic_cx = int(200 * s)
    mic_cy = height // 2
    mic_line_w = max(3, int(4 * s))
    mic_top, mic_mid = _draw_mic_solid(draw, mic_cx, mic_cy, s * 1.5, WHITE_DIM, WHITE, mic_line_w)

    # Fontes
    font_big = _get_handwriting_font(int(90 * s))
    font_sub = _get_handwriting_font(int(30 * s))

    # Posicao do texto
    text_x = int(520 * s)
    text_y = height // 2 - int(65 * s)

    # Curva fluida do microfone ate o texto (voz virando escrita)
    curve_start_x = mic_cx + int(55 * s)
    curve_start_y = mic_mid
    curve_end_x = text_x - int(15 * s)
    curve_end_y = text_y + int(50 * s)

    # Desenhar curva com dots que vao sumindo
    steps = 40
    cp1x = curve_start_x + (curve_end_x - curve_start_x) * 0.35
    cp1y = curve_start_y - int(40 * s)
    cp2x = curve_start_x + (curve_end_x - curve_start_x) * 0.65
    cp2y = curve_end_y + int(30 * s)

    points = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3 * curve_start_x + 3 * mt**2 * t * cp1x + 3 * mt * t**2 * cp2x + t**3 * curve_end_x
        y = mt**3 * curve_start_y + 3 * mt**2 * t * cp1y + 3 * mt * t**2 * cp2y + t**3 * curve_end_y
        points.append((x, y))

    # Linha fluida verde -> branca (transicao voz -> texto)
    for i in range(len(points) - 1):
        t = i / len(points)
        r = int(100 + (240 - 100) * t)
        g = int(210 + (242 - 210) * t)
        b = int(120 + (250 - 120) * t)
        alpha = int(80 + 175 * t)
        seg_w = max(2, int((2 + 2 * t) * s))
        draw.line([points[i], points[i + 1]], fill=(r, g, b, alpha), width=seg_w)

    # Texto principal — "Scribe4me" em handwriting
    draw.text((text_x, text_y), "Scribe4me",
              fill=WHITE, font=font_big)

    # Subtitulo
    draw.text((text_x + int(5 * s), text_y + int(95 * s)),
              "speech-to-text local com IA",
              fill=WHITE_DIM, font=font_sub)

    # Pequenos dots decorativos ao redor da curva
    dot_r = max(1, int(2 * s))
    for i in range(0, len(points), 8):
        t = i / len(points)
        alpha = int(40 + 60 * t)
        x, y = points[i]
        # Dots ligeiramente acima e abaixo da curva
        offset = int(8 * s) * math.sin(i * 0.5)
        draw.ellipse(
            [x - dot_r, y + offset - dot_r, x + dot_r, y + offset + dot_r],
            fill=(100, 210, 120, alpha),
        )

    return img


def main():
    """Gera todos os assets visuais."""
    os.makedirs("assets", exist_ok=True)

    # Gera icone em alta resolucao e faz downscale para melhor antialiasing
    master = create_icon(1024)

    # --- ICO com multiplas resolucoes (downscale do master) ---
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [master.resize((s, s), Image.LANCZOS) for s in sizes]

    # Salva ICO: a maior imagem como principal, menores como append
    images[-1].save(
        "assets/scribe4me.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Icone gerado: assets/scribe4me.ico ({os.path.getsize('assets/scribe4me.ico')} bytes)")

    # --- PNG 256 ---
    master.resize((256, 256), Image.LANCZOS).save("assets/scribe4me_256.png")
    print("PNG 256 gerado: assets/scribe4me_256.png")

    # --- PNG 512 (para GitHub profile/social) ---
    master.resize((512, 512), Image.LANCZOS).save("assets/scribe4me_512.png")
    print("PNG 512 gerado: assets/scribe4me_512.png")

    # --- Banner para README ---
    banner = create_banner()
    banner.save("assets/banner.png")
    print("Banner gerado: assets/banner.png")


if __name__ == "__main__":
    main()
