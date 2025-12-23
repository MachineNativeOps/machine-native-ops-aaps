# 🧹 Step-3: 清理和重組專案結構

## 🎯 任務目標
按照 "minimal system skeleton" 原則重組專案，將所有治理和專案文件移到正確的位置。

---

## 📋 任務清單

### Phase 1: 分析當前結構
- [x] 列出根目錄所有文件
- [x] 分類文件（治理文件、專案文件、配置文件）
- [x] 確定每個文件應該移動到哪裡

### Phase 2: 創建目標結構
- [x] 確保 controlplane/ 結構完整
- [x] 確保 workspace/ 結構完整
- [x] 創建必要的子目錄

### Phase 3: 移動文件
- [x] 移動治理文件到 controlplane/governance/
- [x] 移動專案文件到 workspace/
- [x] 保留根目錄必要文件（README.md, .gitignore, etc.）

### Phase 4: 更新根目錄 README
- [x] 創建簡潔的根目錄 README.md
- [x] 說明專案結構
- [x] 提供導航連結

### Phase 5: 驗證和測試
- [x] 檢查文件移動是否正確
- [x] 運行驗證系統
- [x] 確認沒有破壞任何功能

### Phase 6: Git 提交和清理
- [ ] 提交所有變更
- [ ] 推送到遠端
- [ ] 檢查並關閉不需要的 PR

---

## 🎯 目標結構

```
/workspace/
├── README.md                    # 簡潔的專案說明
├── .gitignore                   # Git 忽略規則
├── .github/                     # GitHub 配置
├── controlplane/                # 治理層（不可變）
│   ├── baseline/                # 基線配置（已完成）
│   ├── overlay/                 # 運行時狀態（已完成）
│   ├── active/                  # 合成視圖（已完成）
│   └── governance/              # 治理文件（新增）
│       ├── docs/                # 治理文檔
│       ├── policies/            # 政策文件
│       └── reports/             # 報告
└── workspace/                   # 工作層（可變）
    ├── projects/                # 專案文件
    ├── docs/                    # 專案文檔
    └── artifacts/               # 構建產物
```

---

## 📊 進度追蹤

**當前階段**: Phase 1 - 分析當前結構  
**完成度**: 0%  
**預計完成時間**: 20-30 分鐘

---

*開始執行 Step-3 任務...*