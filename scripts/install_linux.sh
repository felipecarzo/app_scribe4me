#!/usr/bin/env bash
# Instalador do Scribe4me para Linux.
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/felipecarzo/app_scribe4me/main/scripts/install_linux.sh | bash
#
# O que faz:
#   1. Baixa o AppImage da ultima release do GitHub
#   2. Instala em ~/.local/bin/Scribe4me
#   3. Cria atalho no menu de aplicativos (~/.local/share/applications/)
#   4. Baixa o icone
#   5. Verifica dependencias de sistema e avisa se faltar algo

set -euo pipefail

APP_NAME="Scribe4me"
REPO="felipecarzo/app_scribe4me"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
DESKTOP_DIR="$HOME/.local/share/applications"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[x]${NC} $1"; }

echo ""
echo "========================================="
echo "  ${APP_NAME} — Instalador Linux"
echo "========================================="
echo ""

# --- 1. Verificar dependencias ---
info "Verificando dependencias..."

MISSING=()

# curl ou wget (pra baixar)
if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    MISSING+=("curl ou wget")
fi

# Clipboard (pyperclip precisa de um desses)
if ! command -v xclip >/dev/null 2>&1 && ! command -v xsel >/dev/null 2>&1; then
    MISSING+=("xclip (sudo apt install xclip)")
fi

# Audio (sounddevice precisa do PortAudio)
if ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    MISSING+=("libportaudio2 (sudo apt install libportaudio2)")
fi

# Tray icon (pystray precisa de AppIndicator)
if ! ldconfig -p 2>/dev/null | grep -q libappindicator3 && ! ldconfig -p 2>/dev/null | grep -q libayatana-appindicator3; then
    MISSING+=("libappindicator3 (sudo apt install libappindicator3-1 ou gir1.2-ayatanaappindicator3-0.1)")
fi

if [ ${#MISSING[@]} -gt 0 ]; then
    warn "Dependencias faltando:"
    for dep in "${MISSING[@]}"; do
        echo "     - $dep"
    done
    echo ""
    warn "Instale com: sudo apt install xclip libportaudio2 libappindicator3-1"
    echo ""
    read -rp "Continuar mesmo assim? [s/N] " REPLY
    if [[ ! "$REPLY" =~ ^[sS]$ ]]; then
        error "Instalacao cancelada."
        exit 1
    fi
fi

# --- 2. Detectar URL da ultima release ---
info "Buscando ultima release..."

if command -v curl >/dev/null 2>&1; then
    RELEASE_JSON=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest")
else
    RELEASE_JSON=$(wget -qO- "https://api.github.com/repos/${REPO}/releases/latest")
fi

# Extrai URL do AppImage (sem jq — usa grep+sed)
APPIMAGE_URL=$(echo "$RELEASE_JSON" | grep -o '"browser_download_url":\s*"[^"]*AppImage"' | head -1 | sed 's/.*"browser_download_url":\s*"\(.*\)"/\1/')

if [ -z "$APPIMAGE_URL" ]; then
    error "Nenhum AppImage encontrado na ultima release."
    error "Verifique: https://github.com/${REPO}/releases"
    exit 1
fi

VERSION=$(echo "$RELEASE_JSON" | grep -o '"tag_name":\s*"[^"]*"' | head -1 | sed 's/.*"tag_name":\s*"\(.*\)"/\1/')
info "Versao: ${VERSION}"

# --- 3. Baixar AppImage ---
info "Baixando ${APP_NAME}..."
mkdir -p "$INSTALL_DIR"

APPIMAGE_PATH="${INSTALL_DIR}/${APP_NAME}"

if command -v curl >/dev/null 2>&1; then
    curl -fSL --progress-bar "$APPIMAGE_URL" -o "$APPIMAGE_PATH"
else
    wget --show-progress -qO "$APPIMAGE_PATH" "$APPIMAGE_URL"
fi

chmod +x "$APPIMAGE_PATH"
info "Instalado em: ${APPIMAGE_PATH}"

# --- 4. Baixar icone ---
info "Baixando icone..."
mkdir -p "$ICON_DIR"

ICON_URL="https://raw.githubusercontent.com/${REPO}/main/assets/scribe4me_256.png"
ICON_PATH="${ICON_DIR}/${APP_NAME}.png"

if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$ICON_URL" -o "$ICON_PATH" 2>/dev/null || true
else
    wget -qO "$ICON_PATH" "$ICON_URL" 2>/dev/null || true
fi

# --- 5. Criar .desktop ---
info "Criando atalho no menu..."
mkdir -p "$DESKTOP_DIR"

cat > "${DESKTOP_DIR}/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=Speech-to-text local com Whisper
Exec=${APPIMAGE_PATH} %U
Icon=${APP_NAME}
Categories=Utility;Audio;
Terminal=false
StartupNotify=true
EOF

# Atualiza cache de .desktop (se disponivel)
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# --- 6. Verificar PATH ---
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    warn "~/.local/bin nao esta no seu PATH."
    warn "Adicione ao seu ~/.bashrc ou ~/.zshrc:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# --- Pronto ---
echo ""
echo "========================================="
info "${APP_NAME} ${VERSION} instalado!"
echo ""
echo "  Executar:     ${APP_NAME}"
echo "  Desinstalar:  rm ${APPIMAGE_PATH} ${DESKTOP_DIR}/${APP_NAME}.desktop"
echo "========================================="
echo ""
