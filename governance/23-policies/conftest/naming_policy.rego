package naming

# 命名規範政策 - Namespace 與資源命名驗證

# Namespace 命名規則
deny[msg] {
  input.kind == "Namespace"
  not regex.match("^(team|tenant|feature)-[a-z0-9-]+$", input.metadata.name)
  msg := sprintf("Namespace 名稱 '%s' 不符合規範格式：必須以 team-/tenant-/feature- 開頭，後接小寫字母、數字或連字符", [input.metadata.name])
}

# Namespace 必須包含必要標籤
deny[msg] {
  input.kind == "Namespace"
  not input.metadata.labels["namespace.io/team"]
  msg := "Namespace 缺少必要標籤：namespace.io/team"
}

deny[msg] {
  input.kind == "Namespace"
  not input.metadata.labels["namespace.io/environment"]
  msg := "Namespace 缺少必要標籤：namespace.io/environment"
}

deny[msg] {
  input.kind == "Namespace"
  not input.metadata.labels["namespace.io/lifecycle"]
  msg := "Namespace 缺少必要標籤：namespace.io/lifecycle"
}

# Deployment 命名規則
deny[msg] {
  input.kind == "Deployment"
  not regex.match("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", input.metadata.name)
  msg := sprintf("Deployment 名稱 '%s' 不符合 Kubernetes 命名規範", [input.metadata.name])
}

# Service 必須有明確的 port 名稱
deny[msg] {
  input.kind == "Service"
  port := input.spec.ports[_]
  not port.name
  msg := sprintf("Service '%s' 的 port 必須有名稱定義", [input.metadata.name])
}

# 容器映像必須使用 SHA256 digest 而非 tag
warn[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not contains(container.image, "@sha256:")
  msg := sprintf("容器 '%s' 使用 tag 而非 SHA256 digest，建議使用固定 digest 提高安全性", [container.name])
}

# 資源名稱長度限制
deny[msg] {
  count(input.metadata.name) > 63
  msg := sprintf("資源名稱 '%s' 超過 63 字元限制", [input.metadata.name])
}
