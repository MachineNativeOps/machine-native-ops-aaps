# 🏛️ MachineNativeOps Root Layer Architecture

## 📋 架構概述

本專案採用 **FHS (Filesystem Hierarchy Standard)** 標準的根層架構，將治理配置提升到根層，使其成為系統的**唯一事實來源**。

---

## 🗂️ 根層目錄結構

### 治理配置檔案（根層）
```
MachineNativeOps/
├── root.config.yaml              # 全域基本配置
├── root.governance.yaml          # 治理/權限/策略配置
├── root.modules.yaml             # 模組註冊管理與相依
├── root.super-execution.yaml     # 超級執行/流程定義
├── root.trust.yaml               # 信任/憑證/安全配置
├── root.provenance.yaml          # 來源追溯與元資料
├── root.integrity.yaml           # 整體性驗證規則
├── root.bootstrap.yaml           # 開機與初始化設定
├── root.devices.map              # 裝置檔案對應表
├── root.fs.map                   # 系統層級目錄映射
├── root.kernel.map               # 核心模組/函式庫對應
├── root.env.sh                   # Root 使用者殼層環境
└── root.naming-policy.yaml       # 命名規範政策
```

### 標準 FHS 目錄
```
├── bin/                          # 基本用戶命令二進制檔案
├── sbin/                         # 系統管理二進制檔案
├── etc/                          # 系統配置檔案
├── lib/                          # 共享函式庫
├── var/                          # 變動資料 (log, tmp, cache)
├── usr/                          # 用戶程式 (bin, sbin, lib, share)
├── home/                         # 用戶主目錄
├── tmp/                          # 臨時檔案
├── opt/                          # 可選應用程式
├── srv/                          # 服務資料
└── init.d/                       # 初始化腳本
```

### 專案特定目錄（保持不變）
```
├── src/                          # 原始碼
├── tests/                        # 測試
├── docs/                         # 文檔
├── config/                       # 應用配置
├── scripts/                      # 腳本
├── tools/                        # 工具
├── examples/                     # 範例
├── deploy/                       # 部署
├── ops/                          # 運維
├── governance/                   # 治理
└── archive/                      # 歸檔
```

---

## 🎯 設計原則

### 1. 單一事實來源（Single Source of Truth）
- 所有治理配置在根層，不分散在子目錄
- `root.*` 檔案是系統配置的權威來源
- 避免配置重複和不一致

### 2. FHS 標準遵循
- 遵循 Filesystem Hierarchy Standard 3.0
- 標準目錄結構易於理解和維護
- 與 Unix/Linux 系統慣例一致

### 3. 清晰的職責分離
- **根層配置**: 系統級治理和配置
- **FHS 目錄**: 運行時資料和程式
- **專案目錄**: 應用程式碼和資源

### 4. 可見性優先
- 治理配置在根層直接可見
- 不使用隱藏檔案（無 `.` 前綴）
- 行動裝置友善

---

## 📊 目錄用途說明

### 治理層（Root Layer）

#### 配置檔案
- **root.config.yaml**: 全域系統配置，定義核心參數
- **root.governance.yaml**: RBAC 角色、策略、審核規則
- **root.modules.yaml**: 模組註冊、依賴關係、載入順序
- **root.super-execution.yaml**: 系統引導流程、安全響應
- **root.trust.yaml**: 信任鏈、證書管理、安全配置
- **root.provenance.yaml**: 審計軌跡、來源追溯、元資料
- **root.integrity.yaml**: 雜湊鎖定、偏移檢測、完整性驗證
- **root.bootstrap.yaml**: 5 階段初始化設定

#### 映射檔案
- **root.devices.map**: 200+ 設備映射定義
- **root.fs.map**: 完整目錄結構映射
- **root.kernel.map**: 核心模組與函式庫對應

#### 腳本與政策
- **root.env.sh**: Shell 環境變數、別名、函數
- **root.naming-policy.yaml**: 命名規範與驗證規則

### 系統層（FHS Directories）

#### /bin - 基本命令
- 所有用戶可用的基本命令
- 系統啟動必需的程式
- Shell、檔案操作、文本處理

#### /sbin - 系統管理
- 需要 root 權限的工具
- 系統初始化、修復、恢復
- 網路配置和管理

#### /etc - 配置檔案
- 系統範圍的配置
- 應用程式配置
- 服務啟動腳本

#### /lib - 共享函式庫
- 系統啟動所需的函式庫
- 核心模組
- 動態連結函式庫

#### /var - 變動資料
- 日誌檔案 (/var/log)
- 臨時檔案 (/var/tmp)
- 快取資料 (/var/cache)
- 應用狀態 (/var/lib)

#### /usr - 用戶程式
- 用戶命令 (/usr/bin)
- 系統管理命令 (/usr/sbin)
- 函式庫 (/usr/lib)
- 共享資料 (/usr/share)
- 本地軟體 (/usr/local)

#### /home - 用戶目錄
- 用戶個人檔案
- 用戶配置
- 用戶專案

#### /tmp - 臨時檔案
- 應用程式臨時檔案
- 重啟後可能清空
- 所有用戶可寫

#### /opt - 可選軟體
- 第三方軟體
- 商業軟體
- 大型應用套件

#### /srv - 服務資料
- Web 伺服器資料
- FTP 資料
- Git 儲存庫

#### /init.d - 初始化腳本
- 15 個系統初始化腳本
- 按順序執行 (00-99)
- 系統啟動和配置

---

## 🔄 遷移說明

### 從舊架構遷移

**Before (舊架構):**
```
MachineNativeOps/
├── root/
│   ├── root.config.yaml
│   ├── root.governance.yaml
│   └── ...
└── [其他目錄]
```

**After (新架構):**
```
MachineNativeOps/
├── root.config.yaml          # 提升到根層
├── root.governance.yaml      # 提升到根層
├── bin/                      # 新增 FHS 目錄
├── sbin/                     # 新增 FHS 目錄
├── etc/                      # 新增 FHS 目錄
└── [其他目錄保持不變]
```

### 變更內容
1. ✅ 所有 `root/*` 檔案提升到根層
2. ✅ 建立標準 FHS 目錄結構
3. ✅ 治理文檔移至 `docs/governance/`
4. ✅ 歷史文檔歸檔至 `archive/legacy-root-files/`

---

## 📱 行動裝置友善性

### 優勢
- ✅ 治理配置在根層直接可見
- ✅ 無需 `ls -a` 查看隱藏檔案
- ✅ 目錄結構清晰易懂
- ✅ 快速定位關鍵配置

### 驗證流程
1. 打開 repo 根目錄
2. 直接看到所有 `root.*` 配置
3. 點擊檔案即可查看內容
4. 標準目錄結構易於導航

---

## 🔍 配置查找指南

### 快速查找
- **系統配置**: `root.config.yaml`
- **權限管理**: `root.governance.yaml`
- **模組管理**: `root.modules.yaml`
- **安全配置**: `root.trust.yaml`
- **初始化**: `init.d/` 目錄

### 文檔位置
- **治理文檔**: `docs/governance/`
- **API 文檔**: `docs/api/`
- **架構文檔**: `docs/architecture/`
- **實施指南**: `IMPLEMENTATION_GUIDE.md`

---

## 🚀 系統啟動流程

### 初始化順序
1. **00-init.sh**: 系統基礎初始化
2. **01-governance-init.sh**: 治理系統初始化
3. **02-modules-init.sh**: 模組系統初始化
4. **03-super-execution-init.sh**: 超級執行初始化
5. **04-trust-init.sh**: 信任系統初始化
6. **05-provenance-init.sh**: 追溯系統初始化
7. **06-database-init.sh**: 資料庫初始化
8. **07-config-init.sh**: 配置系統初始化
9. **08-dependencies-init.sh**: 依賴管理初始化
10. **09-logging-init.sh**: 日誌系統初始化
11. **10-security-init.sh**: 安全系統初始化
12. **11-multiplatform-init.sh**: 多平台支援初始化
13. **12-api-gateway-init.sh**: API 閘道初始化
14. **13-services-init.sh**: 服務初始化
15. **99-finalize.sh**: 完成化腳本

---

## 📞 維護資訊

**架構版本**: v2.0.0  
**最後更新**: 2025-12-21  
**維護者**: MachineNativeOps 治理委員會  
**FHS 版本**: 3.0

---

## 🔗 相關文檔

- [治理層 README](docs/governance/ROOT_LAYER_README.md)
- [代理人交付合約](docs/governance/AGENT_DELIVERY_CONTRACT.md)
- [驗證清單](docs/governance/VALIDATION_CHECKLIST.md)
- [實施指南](IMPLEMENTATION_GUIDE.md)
- [FHS 標準](https://refspecs.linuxfoundation.org/FHS_3.0/fhs-3.0.html)

---

*本架構確保 MachineNativeOps 專案具有清晰、標準、可維護的根層結構。*