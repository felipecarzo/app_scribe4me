"""Gera logo e icone profissional para o Scribe4me."""

import math
import os
from PIL import Image, ImageDraw, ImageFont


def _gradient_circle(draw, cx, cy, radius, color_top, color_bottom):
    """Preenche um circulo com gradiente vertical."""
    rt, gt, bt = color_top
    rb, gb, bb = color_bottom
    for y in range(cy - radius, cy + radius + 1):
        t = (y - (cy - radius)) / (2 * radius) if radius > 0 else 0
        r = int(rt + (rb - rt) * t)
        g = int(gt + (gb - gt) * t)
        b = int(bt + (bb - bt) * t)
        # largura horizontal nesse y
        dy = abs(y - cy)
        if dy > radius:
            continue
        half_w = int(math.sqrt(radius * radius - dy * dy))
        draw.line([cx - half_w, y, cx + half_w, y], fill=(r, g, b))


def create_icon(size: int = 256) -> Image.Image:
    """Cria icone moderno: microfone + ondas sonoras + linhas de texto."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    radius = size // 2 - 2
    s = size / 256  # fator de escala

    # --- Fundo circular com gradiente ---
    _gradient_circle(draw, cx, cy, radius, (26, 35, 126), (13, 71, 161))

    # Anel externo sutil
    ring_w = max(2, int(3 * s))
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=(66, 165, 245, 120),
        width=ring_w,
    )

    # --- Microfone (lado esquerdo do centro) ---
    mic_cx = cx - int(30 * s)

    # Corpo do microfone
    mic_w = int(44 * s)
    mic_h = int(68 * s)
    mic_x = mic_cx - mic_w // 2
    mic_y = int(52 * s)
    mic_r = int(22 * s)

    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
        radius=mic_r,
        fill=(232, 234, 246),
    )

    # Grades do microfone
    grid_color = (121, 134, 203)
    grid_w = max(1, int(2 * s))
    for i in range(4):
        gy = mic_y + int((20 + i * 13) * s)
        draw.line(
            [mic_x + int(8 * s), gy, mic_x + mic_w - int(8 * s), gy],
            fill=grid_color,
            width=grid_w,
        )

    # Arco U (suporte)
    arc_w = int(64 * s)
    arc_h = int(40 * s)
    arc_x = mic_cx - arc_w // 2
    arc_y = mic_y + mic_h - int(12 * s)
    arc_line_w = max(3, int(4 * s))
    draw.arc(
        [arc_x, arc_y, arc_x + arc_w, arc_y + arc_h * 2],
        start=0, end=180,
        fill=(200, 210, 240),
        width=arc_line_w,
    )

    # Haste vertical
    haste_w = max(2, int(4 * s))
    haste_top = arc_y + arc_h
    haste_bottom = haste_top + int(20 * s)
    draw.line([mic_cx, haste_top, mic_cx, haste_bottom],
              fill=(200, 210, 240), width=haste_w)

    # Base
    base_hw = int(20 * s)
    draw.line([mic_cx - base_hw, haste_bottom, mic_cx + base_hw, haste_bottom],
              fill=(200, 210, 240), width=haste_w)

    # --- Ondas sonoras (saindo do microfone pra direita) ---
    wave_color_1 = (76, 175, 80, 200)   # verde
    wave_color_2 = (76, 175, 80, 140)
    wave_color_3 = (76, 175, 80, 80)
    wave_w = max(2, int(3 * s))

    wave_cx = mic_cx + int(30 * s)
    wave_cy = mic_y + mic_h // 2

    # 3 arcos concentricos
    for i, color in enumerate([wave_color_1, wave_color_2, wave_color_3]):
        r = int((18 + i * 16) * s)
        draw.arc(
            [wave_cx - r, wave_cy - r, wave_cx + r, wave_cy + r],
            start=-45, end=45,
            fill=color,
            width=wave_w,
        )

    # --- Linhas de texto (lado direito, representando transcricao) ---
    text_color_bright = (232, 234, 246)
    text_color_dim = (144, 164, 210)
    text_x = cx + int(20 * s)
    text_start_y = int(80 * s)
    line_h = int(14 * s)
    line_thick = max(2, int(4 * s))
    line_r = max(1, int(2 * s))

    # Linhas de diferentes tamanhos simulando texto
    line_widths = [0.80, 0.65, 0.90, 0.55, 0.72]
    max_line_w = int(85 * s)

    for i, ratio in enumerate(line_widths):
        ly = text_start_y + i * int(20 * s)
        lw = int(max_line_w * ratio)
        color = text_color_bright if i < 3 else text_color_dim
        draw.rounded_rectangle(
            [text_x, ly, text_x + lw, ly + line_thick],
            radius=line_r,
            fill=color,
        )

    # --- Seta / fluxo do mic pro texto (ponto de ligacao visual) ---
    arrow_color = (76, 175, 80, 160)
    arrow_y = wave_cy
    arrow_x1 = wave_cx + int(30 * s)
    arrow_x2 = text_x - int(8 * s)

    if size >= 64:  # so desenha em tamanhos maiores
        # Pequenos dots de transicao
        dot_r = max(1, int(2 * s))
        for j in range(3):
            dx = arrow_x1 + (arrow_x2 - arrow_x1) * j // 3
            draw.ellipse(
                [dx - dot_r, arrow_y - dot_r, dx + dot_r, arrow_y + dot_r],
                fill=arrow_color,
            )

    return img


def create_banner(width: int = 1280, height: int = 640) -> Image.Image:
    """Cria banner para o README do GitHub."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo com gradiente horizontal
    for x in range(width):
        t = x / width
        r = int(13 + (26 - 13) * t)
        g = int(71 + (35 - 71) * t)
        b = int(161 + (126 - 161) * t)
        draw.line([x, 0, x, height], fill=(r, g, b))

    # Icone grande no centro-esquerdo
    icon = create_icon(320)
    icon_x = width // 4 - 160
    icon_y = height // 2 - 160
    img.paste(icon, (icon_x, icon_y), icon)

    # Texto "Scribe4me" ao lado
    text_x = width // 2 - 40
    text_y_title = height // 2 - 60

    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 72)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeuil.ttf", 28)
    except (OSError, IOError):
        try:
            font_title = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 72)
            font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
        except (OSError, IOError):
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

    draw.text((text_x, text_y_title), "Scribe4me",
              fill=(232, 234, 246), font=font_title)
    draw.text((text_x, text_y_title + 85), "Speech-to-text local com IA",
              fill=(144, 164, 210), font=font_sub)

    return img


def main():
    """Gera todos os assets visuais."""
    os.makedirs("assets", exist_ok=True)

    # --- ICO com multiplas resolucoes ---
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    images[0].save(
        "assets/scribe4me.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print("Icone gerado: assets/scribe4me.ico")

    # --- PNG 256 ---
    images[-1].save("assets/scribe4me_256.png")
    print("PNG 256 gerado: assets/scribe4me_256.png")

    # --- PNG 512 (para GitHub profile/social) ---
    icon_512 = create_icon(512)
    icon_512.save("assets/scribe4me_512.png")
    print("PNG 512 gerado: assets/scribe4me_512.png")

    # --- Banner para README ---
    banner = create_banner()
    banner.save("assets/banner.png")
    print("Banner gerado: assets/banner.png")


if __name__ == "__main__":
    main()
