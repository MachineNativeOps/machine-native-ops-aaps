#!/bin/bash

# Optimized setup for codespace - prevents hanging at 93%
# This script runs automatically when the codespace is created
set -e

echo "🔧 Keystone Platform - 開發環境自動初始化"
echo "📅 開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 檢查必要工具
echo "📋 驗證開發環境工具鏈..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安裝"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm 未安裝"; exit 1; }

echo "✅ 基礎工具鏈驗證通過"
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"
echo ""

# 創建必要的開發目錄
echo "📁 創建開發目錄結構..."
mkdir -p .vscode
mkdir -p scripts
mkdir -p tests/integration
mkdir -p logs
echo "✅ 目錄創建完成"
echo ""

# 設置開發環境變數
echo "⚙️ 配置環境變數..."
if [ ! -f .env.local ]; then
    if [ -f .env.example ]; then
        cp .env.example .env.local
        echo "✅ 環境變數模板已創建: .env.local"
    else
        echo "⚠️  .env.example 不存在，跳過環境變數配置"
    fi
else
    echo "✅ .env.local 已存在"
fi
echo ""

# 優化的 npm 安裝 - 防止卡住
echo "📦 自動安裝項目依賴..."
echo "💡 使用優化設定以避免在 93% 處卡住"
echo ""

# 配置 npm 以提高性能和穩定性
# 注意：這些設定只影響當前會話，不會永久修改全局配置
echo "🔧 配置 npm 參數..."
export NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000
export NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000
export NPM_CONFIG_FETCH_RETRIES=3
export NPM_CONFIG_LOGLEVEL=error
echo "✅ npm 配置完成"
echo ""

# 定義通用的 npm 安裝選項
NPM_INSTALL_OPTS="--prefer-offline --no-audit --progress=false"

# 檢查 package-lock.json 是否存在
if [ -f package-lock.json ]; then
    echo "📦 檢測到 package-lock.json，使用 npm ci 進行安裝..."
    echo "⏳ 正在安裝（這可能需要 1-2 分鐘）..."
    
    # 嘗試 npm ci，如果失敗則降級到 npm install
    if npm ci $NPM_INSTALL_OPTS 2>&1 | tee /tmp/npm-install.log; then
        echo "✅ npm ci 安裝成功"
    else
        echo "⚠️  npm ci 失敗，嘗試使用 npm install..."
        if npm install $NPM_INSTALL_OPTS 2>&1 | tee /tmp/npm-install.log; then
            echo "✅ npm install 安裝成功"
        else
            echo "❌ npm 安裝失敗，請查看日誌: /tmp/npm-install.log"
            exit 1
        fi
    fi
else
    echo "📦 未檢測到 package-lock.json，使用 npm install 安裝..."
    echo "⏳ 正在安裝（這可能需要 1-2 分鐘）..."
    
    if npm install $NPM_INSTALL_OPTS 2>&1 | tee /tmp/npm-install.log; then
        echo "✅ npm install 安裝成功"
    else
        echo "❌ npm 安裝失敗，請查看日誌: /tmp/npm-install.log"
        exit 1
    fi
fi

echo ""
echo "📊 安裝統計:"
npm list --depth=0 2>/dev/null | head -5 || echo "   已安裝 $(ls node_modules 2>/dev/null | wc -l) 個套件"

echo ""
echo "✅ 開發環境自動配置完成!"
echo "📅 完成時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "🎉 程式碼空間已就緒！"
echo ""
echo "🚀 自動啟動的服務:"
echo "   ✓ 開發伺服器將在容器啟動後自動運行"
echo "   ✓ 訪問 http://localhost:3000 查看應用"
echo ""
echo "📝 可用指令:"
echo "   npm run dev   - 手動啟動開發伺服器"
echo "   npm run build - 構建項目"
echo "   npm run test  - 運行測試"
echo ""
echo "🔧 可選工具:"
echo "   bash .devcontainer/install-optional-tools.sh"
echo "   （安裝 Trivy, Cosign, Syft, OPA, Conftest）"
echo ""
echo "📚 查看 .devcontainer/README.md 了解更多"
echo ""