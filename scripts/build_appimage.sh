#!/usr/bin/env bash
# Build script para gerar o AppImage do Scribe4me no Linux.
#
# Pre-requisitos:
#   - Python 3.12 com pip (venv recomendado)
#   - appimagetool (https://github.com/AppImage/appimagetool)
#   - Dependencias de sistema: libportaudio2, libappindicator3-1 (ou ayatana)
#
# Uso:
#   chmod +x scripts/build_appimage.sh
#   ./scripts/build_appimage.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="Scribe4me"
APPDIR="$PROJECT_DIR/build_linux/${APP_NAME}.AppDir"

echo "=== ${APP_NAME} — Build AppImage ==="

# 1. PyInstaller
echo "[1/4] Rodando PyInstaller..."
cd "$PROJECT_DIR"
pyinstaller --clean --noconfirm scribe4me_linux.spec

# 2. Montar AppDir
echo "[2/4] Montando AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copia output do PyInstaller
cp -r "dist/${APP_NAME}"/* "$APPDIR/usr/bin/"

# Icone
cp "assets/scribe4me_256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
cp "assets/scribe4me_256.png" "$APPDIR/${APP_NAME}.png"

# 3. .desktop file
echo "[3/4] Criando .desktop e AppRun..."
cat > "$APPDIR/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=usr/bin/${APP_NAME}
Icon=${APP_NAME}
Categories=Utility;Audio;
Comment=Speech-to-text local com Whisper
Terminal=false
EOF

# AppRun
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="$(dirname "$SELF")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH:-}"
exec "${HERE}/usr/bin/Scribe4me" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# 4. Gerar AppImage
echo "[4/4] Gerando AppImage..."
OUTPUT="$PROJECT_DIR/dist/${APP_NAME}-x86_64.AppImage"

if command -v appimagetool >/dev/null 2>&1; then
    ARCH=x86_64 appimagetool "$APPDIR" "$OUTPUT"
    echo ""
    echo "=== AppImage gerado: $OUTPUT ==="
    echo "Tamanho: $(du -h "$OUTPUT" | cut -f1)"
else
    echo "ERRO: appimagetool nao encontrado no PATH."
    echo "Instale: https://github.com/AppImage/appimagetool/releases"
    echo ""
    echo "O AppDir foi montado em: $APPDIR"
    echo "Quando tiver o appimagetool, rode:"
    echo "  ARCH=x86_64 appimagetool '$APPDIR' '$OUTPUT'"
    exit 1
fi
