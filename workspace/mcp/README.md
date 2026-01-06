# MachineNativeOps Unified Pipeline & MCP Integration (world_class_validation baseline)

> Note: This subproject holds MCP integration + unified pipeline assets grounded on the world_class_validation baseline. It ships executable YAML manifest, JSON Schema, TypeScript types, and a Python loader.

## Architecture
```mermaid
graph TB
  subgraph "輸入統一層"
      I1[GitHub/GitLab Webhook]
      I2[MCP 協議接口]
      I3[CLI 命令輸入]
      I4[API REST/gRPC]
      I5[事件總線訂閱]
  end

  subgraph "核心調度引擎"
      C1[統一事件路由器]
      C2[即時任務分解器]
      C3[資源競合調解器]
      C4[動態負載均衡器]
      C5[同步屏障控制器]
  end

  subgraph "執行管線層"
      P1[量子驗證管線]
      P2[重構執行管線]
      P3[安全合規管線]
      P4[部署交付管線]
      P5[監控告警管線]
  end

  subgraph "MCP 集成層"
      M1[MCP 服務器]
      M2[工具協議適配]
      M3[資源管理接口]
      M4[實時同步引擎]
      M5[跨平台協調器]
  end

  subgraph "輸出統一層"
      O1[統一審計日誌]
      O2[證據鏈聚合]
      O3[狀態報告生成]
      O4[自動修復觸發]
      O5[多平台通知]
  end

  I1 & I2 & I3 & I4 & I5 --> C1
  C1 --> C2 --> C3 --> C4 --> C5
  C5 --> P1 & P2 & P3 & P4 & P5
  P1 & P2 & P3 & P4 & P5 --> M1
  M1 --> M2 & M3 & M4 & M5
  M2 & M3 & M4 & M5 --> O1 & O2 & O3 & O4 & O5
```

## Key artifacts
- YAML manifest: `workspace/mcp/pipelines/unified-pipeline-config.yaml`
- JSON Schema: `workspace/mcp/schemas/unified-pipeline.schema.json`
- TypeScript types: `workspace/mcp/types/unifiedPipeline.ts`
- Python loader: `workspace/mcp/tools/load_unified_pipeline.py`

## Quick notes
- JSON Schema can be used in CI for early validation.
- Python loader provides typed access for MCP server integration.
- TypeScript types can be imported directly in MCP tool implementations.
