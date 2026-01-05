# MachineNativeOps

本倉庫同時包含：

- **AAPS Root Layer**：以 Linux FHS 風格落地的最小根層骨架，並將治理配置集中到 `controlplane/`。
- **CI/CD System**：以 GitHub Actions 為核心的企業級交付流水線，包含安全掃描、驗證閘門、Cloudflare 部署等。

若你是第一次進來：先看「AAPS Root Layer」理解目錄邊界，再看「CI/CD System」了解交付與驗證機制。

---

## 🎯 當前焦點

- 專案已鎖定執行既定的三階段重構計劃（解構 → 集成 → 重構），詳見 `INSTANT-EXECUTION-REFACTOR-PLAN.md` 與 `workspace/docs/refactor_playbooks/README.md`
- 所有工作優先支持架構重構與自動化執行，不引入與計劃無關的需求

---

## 🏗️ AAPS Root Layer

## 🏗️ 架構概述

本項目採用「類 Linux 最小系統骨架」+ Controlplane 分離架構。

### 根層結構（極簡化）

```
machine-native-ops-aaps/
├── bin/                    # 基本用戶命令二進制檔案
├── sbin/                   # 系統管理二進制檔案
├── etc/                    # 系統配置檔案
├── lib/                    # 共享函式庫
├── var/                    # 變動資料
├── usr/                    # 用戶程式
├── home/                   # 用戶主目錄
├── tmp/                    # 臨時檔案
├── opt/                    # 可選應用程式
├── srv/                    # 服務資料
├── init.d/                 # 初始化腳本
│
├── controlplane/           # 治理控制層（唯讀）
│   ├── config/            # 配置文件
│   ├── specifications/    # 規格定義
│   ├── registries/        # 註冊表
│   ├── validation/        # 驗證工具
│   ├── integration/       # 集成配置
│   └── documentation/     # 文檔
│
├── workspace/              # 工作區（讀寫）
│   ├── src/               # 源代碼
│   ├── docs/              # 項目文檔
│   ├── scripts/           # 腳本工具
│   ├── tests/             # 測試
│   └── ...                # 其他項目文件
│
├── root.bootstrap.yaml     # 引導配置
├── root.fs.map            # 文件系統映射
└── root.env.sh            # 環境變數
```

---

## 🚀 快速開始

### 1. 加載環境

```bash
source root.env.sh
```

### 2. 驗證結構

```bash
# 檢查 controlplane
ls -la ${CONTROLPLANE_PATH}

# 檢查 workspace
ls -la ${WORKSPACE_PATH}
```

### 3. 開始工作

```bash
# 進入工作區
cd workspace/

# 查看項目文檔
cd docs/

# 運行測試
cd tests/
pytest
```

---

## 🔁 CI/CD System

此 repo 內建完整的 CI/CD 與治理閘門（多數工作流在 `.github/workflows/`），常用入口如下：

- `workspace/scripts/`：CI/CD 與維運腳本（驗證、部署、命名遷移、健康檢查等）
- `workspace/docs/`：交付/治理/操作手冊
- `cloudflare/`：Cloudflare Pages / Workers 相關配置與專案

**Key Features**（高層概覽）：

- Automated CI/CD pipeline（GitHub Actions）
- Progressive / canary deployment workflows
- Intelligent rollback / drill simulation tooling
- Security & compliance gates（含供應鏈/簽章/掃描等）

---

## 📁 目錄說明

### FHS 標準目錄

| 目錄      | 用途         | 權限 |
| --------- | ------------ | ---- |
| `bin/`    | 基本用戶命令 | 755  |
| `sbin/`   | 系統管理命令 | 755  |
| `etc/`    | 系統配置     | 755  |
| `lib/`    | 共享庫       | 755  |
| `var/`    | 變動數據     | 755  |
| `usr/`    | 用戶程式     | 755  |
| `home/`   | 用戶目錄     | 755  |
| `tmp/`    | 臨時文件     | 1777 |
| `opt/`    | 可選軟件     | 755  |
| `srv/`    | 服務數據     | 755  |
| `init.d/` | 初始化腳本   | 755  |

### Controlplane（治理層）

**路徑**: `./controlplane`  
**模式**: 只讀（運行時）  
**用途**: 集中管理所有治理、配置、規格文件

```
controlplane/
├── config/              # 核心配置
│   ├── root.config.yaml
│   ├── root.governance.yaml
│   ├── root.modules.yaml
│   └── ...
├── specifications/      # 規格定義
├── registries/          # 模塊註冊
├── validation/          # 驗證工具
├── integration/         # 集成配置
└── documentation/       # 治理文檔
```

### Workspace（工作區）

**路徑**: `./workspace`  
**模式**: 讀寫  
**用途**: 所有項目開發文件

```
workspace/
├── src/                 # 源代碼
├── docs/                # 項目文檔
├── scripts/             # 腳本工具
├── tests/               # 測試文件
├── tools/               # 開發工具
├── examples/            # 示例代碼
└── ...                  # 其他項目文件
```

---

## 🔧 引導文件

### root.bootstrap.yaml

定義 controlplane 的入口、版本和啟動模式。

```yaml
controlplane:
  path: "./controlplane"
  versionLock:
    controlplaneVersion: "v1.0.0"
bootMode:
  mode: "production"
```

### root.fs.map

定義文件系統掛載和映射關係。

```yaml
mounts:
  - name: controlplane
    from: "./controlplane"
    to: "/controlplane"
    mode: "ro"
```

### root.env.sh

定義環境變數。

```bash
export CONTROLPLANE_PATH="./controlplane"
export WORKSPACE_PATH="./workspace"
```

---

## 📚 文檔

- **重構報告**: `workspace/PROJECT_RESTRUCTURE_REPORT.md`
- **開發指南**: `workspace/docs/`
- **API 文檔**: `workspace/docs/api/`
- **治理文檔**: `controlplane/documentation/`

---

## 🔍 常見任務

### 查看配置

```bash
# 查看治理配置
cat ${CONTROLPLANE_CONFIG}/root.governance.yaml

# 查看模塊註冊
cat ${CONTROLPLANE_REGISTRIES}/root.registry.modules.yaml
```

### 運行驗證

```bash
# 運行結構驗證
python ${CONTROLPLANE_VALIDATION}/verify_refactoring.py

# 運行供應鏈驗證
python ${CONTROLPLANE_VALIDATION}/supply-chain-complete-verifier.py
```

### 開發工作

```bash
# 進入源碼目錄
cd ${WORKSPACE_PATH}/src/

# 運行測試
cd ${WORKSPACE_PATH}/tests/
pytest

# 查看文檔
cd ${WORKSPACE_PATH}/docs/
```

---

## ⚠️ 重要提示

### 路徑更新

所有代碼中的路徑引用需要更新：

**舊路徑**:

```python
config = "root.config.yaml"
```

**新路徑**:

```python
config = "controlplane/config/root.config.yaml"
# 或使用環境變數
config = os.path.join(os.environ['CONTROLPLANE_CONFIG'], 'root.config.yaml')
```

### Controlplane 只讀

運行時 controlplane 應該是只讀的。更新配置應該通過：

1. CI/CD 流程
2. 受控的配置管理工具
3. 版本控制系統

### Workspace 隔離

所有開發工作應該在 workspace 中進行，不要直接修改根層或 controlplane。

---

## 🎯 設計原則

1. **職責分離**: 根層（骨架）、Controlplane（治理）、Workspace（開發）
2. **FHS 標準**: 完全符合 Linux FHS 3.0 標準
3. **最小化根層**: 根層只保留必要的骨架和引導文件
4. **集中治理**: 所有治理文件集中在 controlplane
5. **開發友好**: 清晰的目錄結構，易於導航和維護

---

## 📊 架構優勢

- ✅ **清晰的職責分離**: 每個層級職責明確
- ✅ **符合 Linux 標準**: 與 Linux 系統一致
- ✅ **易於維護**: 邏輯分組清晰
- ✅ **可擴展性**: 易於添加新功能
- ✅ **安全性**: Controlplane 只讀保護

---

## 🔗 相關資源

- **FHS 標準**: https://refspecs.linuxfoundation.org/FHS_3.0/
- **項目文檔**: `workspace/docs/`
- **重構報告**: `workspace/PROJECT_RESTRUCTURE_REPORT.md`

---

**版本**: v1.0.0  
**最後更新**: 2024-12-23  
**維護者**: MachineNativeOps Team
