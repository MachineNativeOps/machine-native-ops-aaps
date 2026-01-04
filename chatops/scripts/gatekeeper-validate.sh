#!/usr/bin/env bash
# ==============================================================================
# 🚪 Gatekeeper Validate - 閘門驗證腳本
# ==============================================================================
# 用途: 本地驗證 PR 閘門要求
# 使用: ./gatekeeper-validate.sh [PR_BODY_FILE]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GATE_ENFORCER="$REPO_ROOT/.github/scripts/gate-enforcer.py"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查 Python 環境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安裝"
        exit 1
    fi
}

# 主函數
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           🚪 Gatekeeper Validate - 閘門驗證                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    check_python

    # 檢查閘門強制器是否存在
    if [[ ! -f "$GATE_ENFORCER" ]]; then
        log_error "閘門強制器不存在: $GATE_ENFORCER"
        exit 1
    fi

    # 獲取 PR body
    PR_BODY_FILE="${1:-}"

    if [[ -n "$PR_BODY_FILE" && -f "$PR_BODY_FILE" ]]; then
        log_info "從檔案讀取 PR 描述: $PR_BODY_FILE"
        python3 "$GATE_ENFORCER" \
            --pr-body-file "$PR_BODY_FILE" \
            --output markdown \
            --repo-root "$REPO_ROOT"
    else
        log_info "從 PULL_REQUEST_TEMPLATE.md 模擬驗證"

        # 使用 PR 模板作為示例
        TEMPLATE="$REPO_ROOT/.github/PULL_REQUEST_TEMPLATE.md"
        if [[ -f "$TEMPLATE" ]]; then
            python3 "$GATE_ENFORCER" \
                --pr-body-file "$TEMPLATE" \
                --output markdown \
                --repo-root "$REPO_ROOT"
        else
            log_warning "無法找到 PR 模板"
            echo ""
            echo "使用方式:"
            echo "  $0 <pr-body-file>      # 驗證指定檔案"
            echo "  $0                      # 使用 PR 模板進行模擬驗證"
            exit 1
        fi
    fi

    exit_code=$?

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "閘門驗證完成"
    else
        log_error "閘門驗證失敗 (exit code: $exit_code)"
    fi

    exit $exit_code
}

main "$@"
