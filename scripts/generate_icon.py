"""Gera icone .ico profissional para o Scribe4me."""

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int = 256) -> Image.Image:
    """Cria icone com microfone estilizado sobre fundo gradiente."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo circular com gradiente (azul escuro -> azul medio)
    cx, cy = size // 2, size // 2
    radius = size // 2 - 2

    # Circulo de fundo — azul profissional
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill="#1a237e",  # azul escuro
    )

    # Anel sutil
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline="#3949ab",
        width=max(2, size // 64),
    )

    # Escala relativa ao tamanho
    s = size / 256

    # --- Microfone ---

    # Corpo do microfone (retangulo arredondado)
    mic_w = int(56 * s)
    mic_h = int(80 * s)
    mic_x = cx - mic_w // 2
    mic_y = int(50 * s)
    mic_r = int(28 * s)  # raio do topo arredondado

    # Topo arredondado do microfone
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
        radius=mic_r,
        fill="#e8eaf6",  # azul muito claro
    )

    # Linhas do microfone (grades)
    line_color = "#7986cb"
    line_w = max(1, int(2 * s))
    for i in range(3):
        y = mic_y + int((28 + i * 16) * s)
        draw.line(
            [mic_x + int(10 * s), y, mic_x + mic_w - int(10 * s), y],
            fill=line_color,
            width=line_w,
        )

    # Arco U embaixo do microfone (suporte)
    arc_w = int(80 * s)
    arc_h = int(50 * s)
    arc_x = cx - arc_w // 2
    arc_y = mic_y + mic_h - int(15 * s)
    arc_line_w = max(3, int(5 * s))

    draw.arc(
        [arc_x, arc_y, arc_x + arc_w, arc_y + arc_h * 2],
        start=0,
        end=180,
        fill="#e8eaf6",
        width=arc_line_w,
    )

    # Haste vertical
    haste_w = max(3, int(5 * s))
    haste_top = arc_y + arc_h
    haste_bottom = haste_top + int(25 * s)
    draw.line(
        [cx, haste_top, cx, haste_bottom],
        fill="#e8eaf6",
        width=haste_w,
    )

    # Base horizontal
    base_w = int(50 * s)
    draw.line(
        [cx - base_w // 2, haste_bottom, cx + base_w // 2, haste_bottom],
        fill="#e8eaf6",
        width=haste_w,
    )

    # --- Ondas sonoras ---
    wave_color = "#4CAF50"  # verde — estado pronto
    wave_w = max(2, int(3 * s))

    # Onda pequena (esquerda)
    draw.arc(
        [int(30 * s), int(60 * s), int(70 * s), int(120 * s)],
        start=220,
        end=320,
        fill=wave_color,
        width=wave_w,
    )

    # Onda grande (esquerda)
    draw.arc(
        [int(15 * s), int(45 * s), int(65 * s), int(135 * s)],
        start=220,
        end=320,
        fill=wave_color,
        width=wave_w,
    )

    # Onda pequena (direita)
    draw.arc(
        [size - int(70 * s), int(60 * s), size - int(30 * s), int(120 * s)],
        start=220,
        end=320,
        fill=wave_color,
        width=wave_w,
    )

    # Onda grande (direita)
    draw.arc(
        [size - int(65 * s), int(45 * s), size - int(15 * s), int(135 * s)],
        start=220,
        end=320,
        fill=wave_color,
        width=wave_w,
    )

    return img


def main():
    """Gera o .ico com multiplas resolucoes."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    # Salvar como .ico
    output = "assets/scribe4me.ico"
    import os
    os.makedirs("assets", exist_ok=True)

    images[0].save(
        output,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icone gerado: {output}")

    # Salvar PNG grande para referencia
    images[-1].save("assets/scribe4me_256.png")
    print("PNG gerado: assets/scribe4me_256.png")


if __name__ == "__main__":
    main()
