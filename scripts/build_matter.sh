#!/usr/bin/env bash
# Matter chip-tool 自动编译脚本（v2.3）
# 自动化 connectedhomeip 源码编译 + 装到 /usr/local/bin
#
# 支持：Linux / macOS / WSL2 / Docker
# 用法：
#   ./scripts/build_matter.sh
#   ./scripts/build_matter.sh docker   # 用 Docker 跑
#   ./scripts/build_matter.sh clean    # 清理

set -e

PROJECT_NAME="connectedhomeip"
REPO_URL="https://github.com/project-chip/${PROJECT_NAME}.git"
WORK_DIR="${HOME}/.cache/myhome-matter"
OUTPUT_DIR="${WORK_DIR}/out"
PLATFORM="${PLATFORM:-raspbian-x64}"
INSTALL_PATH="${INSTALL_PATH:-/usr/local/bin/chip-tool}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_cmd() {
    command -v "$1" >/dev/null 2>&1 || {
        log_error "依赖缺失: $1"
        return 1
    }
}

build_docker() {
    log_info "🎯 Docker 模式编译 chip-tool"
    mkdir -p "$WORK_DIR"
    docker run -it --rm \
        -v "${WORK_DIR}:/work" \
        -w /work \
        ubuntu:22.04 \
        bash -c "
            apt-get update && apt-get install -y --no-install-recommends \
                git ca-certificates gcc g++ pkg-config libssl-dev \
                libdbus-1-dev libglib2.0-dev libavahi-client-dev \
                ninja-build python3 python3-pip
            git clone --depth 1 ${REPO_URL}
            cd ${PROJECT_NAME}
            git submodule update --init --recursive
            ./scripts/bootstrap.sh
            ./scripts/build.sh
            mkdir -p /work/out
            find out -name chip-tool -type f -exec cp {} /work/out/ \;
            ls /work/out/
        "
    log_info "Docker 编译完成 → ${OUTPUT_DIR}"
}

build_linux() {
    log_info "🐧 Linux 模式编译 chip-tool"
    if ! check_cmd git; then log_error "git 未装"; return 1; fi
    if ! check_cmd gcc && ! check_cmd clang; then
        log_error "gcc / clang 未装"
        return 1
    fi

    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    if [ ! -d "$PROJECT_NAME" ]; then
        log_info "克隆 connectedhomeip（~500MB）..."
        git clone --depth 1 "$REPO_URL"
    fi

    cd "$PROJECT_NAME"
    git submodule update --init --recursive

    log_info "安装依赖..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y --no-install-recommends \
                    libssl-dev libdbus-1-dev libglib2.0-dev \
                    libavahi-client-dev ninja-build python3 python3-pip
                ;;
            fedora|rhel|centos)
                sudo dnf install -y openssl-devel dbus-devel glib2-devel \
                    avahi-devel ninja-build python3 python3-pip
                ;;
            arch)
                sudo pacman -S --noconfirm openssl dbus glib2 avahi ninja python python-pip
                ;;
        esac
    fi

    log_info "Bootstrap（拉依赖，5-10 分钟）..."
    ./scripts/bootstrap.sh

    log_info "编译（30-60 分钟）..."
    ./scripts/build.sh

    mkdir -p "$OUTPUT_DIR"
    find out -name chip-tool -type f -exec cp {} "$OUTPUT_DIR" \;
    log_info "编译完成 → ${OUTPUT_DIR}"
}

build_macos() {
    log_info "🍎 macOS 模式编译"
    if ! check_cmd brew; then
        log_error "需 Homebrew（/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"）"
        return 1
    fi
    brew install openssl@3 pkg-config glib dbus

    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
    if [ ! -d "$PROJECT_NAME" ]; then
        git clone --depth 1 "$REPO_URL"
    fi
    cd "$PROJECT_NAME"
    git submodule update --init --recursive
    ./scripts/bootstrap.sh
    ./scripts/build.sh
    mkdir -p "$OUTPUT_DIR"
    find out -name chip-tool -type f -exec cp {} "$OUTPUT_DIR" \;
    log_info "编译完成"
}

install() {
    if [ ! -f "$OUTPUT_DIR/chip-tool" ]; then
        log_error "chip-tool 未生成：$OUTPUT_DIR/chip-tool"
        return 1
    fi
    if [ "$EUID" -eq 0 ]; then
        cp "$OUTPUT_DIR/chip-tool" "$INSTALL_PATH"
        chmod +x "$INSTALL_PATH"
    elif command -v sudo >/dev/null 2>&1; then
        sudo cp "$OUTPUT_DIR/chip-tool" "$INSTALL_PATH"
        sudo chmod +x "$INSTALL_PATH"
    else
        log_warn "需 root：cp $OUTPUT_DIR/chip-tool /usr/local/bin/ 手动"
        INSTALL_PATH="$OUTPUT_DIR/chip-tool"
    fi
    log_info "✅ chip-tool 已装 → $INSTALL_PATH"
}

verify() {
    if "$INSTALL_PATH" --version 2>&1 | head -1; then
        log_info "✅ 验证通过"
        return 0
    fi
    log_warn "⚠️  验证失败（可能 chip-tool 编译未完成）"
    return 1
}

# ============================================================
# 主流程
# ============================================================

case "${1:-native}" in
    docker)
        build_docker
        install
        verify
        ;;
    clean)
        rm -rf "$WORK_DIR"
        log_info "清理完成：$WORK_DIR"
        ;;
    native|*)
        OS=$(uname -s)
        case "$OS" in
            Linux)
                build_linux
                ;;
            Darwin)
                build_macos
                ;;
            *)
                log_warn "未识别的 OS：$OS，使用 Docker 模式"
                build_docker
                ;;
        esac
        install
        verify
        ;;
esac
