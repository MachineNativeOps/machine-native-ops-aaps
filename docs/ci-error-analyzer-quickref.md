# CI Error Analyzer - Quick Reference

## 🚀 Quick Start

The CI Error Analyzer automatically runs when your workflows fail. No setup needed!

## 📊 What You Get

When a CI workflow fails, the analyzer automatically:

1. **Downloads failure logs** from GitHub Actions
2. **Analyzes errors** using pattern matching
3. **Posts PR comments** with error summary and suggestions
4. **Creates issues** for critical errors

## 🔍 Understanding the Analysis Report

### PR Comment Structure

```markdown
# 🔍 CI Error Analysis Report

## 📊 Summary
- **Total Errors**: 5
- **Auto-Fixable**: 2

### Errors by Category
- **build_error**: 3
- **lint_error**: 2

### Top Errors

1. TypeScript compilation error
   - Category: type_error
   - Severity: high
   - File: `src/index.ts:42`
   - 💡 Suggestion: Check type definitions and imports
```

### Error Categories

| Icon | Category | Meaning | Typical Action |
|------|----------|---------|----------------|
| 🔴 | Build Error | Compilation/build failed | Fix syntax/imports |
| 🟠 | Test Failure | Tests didn't pass | Fix test logic |
| 🟡 | Lint Error | Code style violation | Run linter fix |
| 🔵 | Type Error | Type checking failed | Fix types |
| 🟣 | Dependency Error | Package issue | Update dependencies |
| ⚫ | Security Scan | Vulnerability found | Update packages |

### Severity Levels

| Icon | Level | Meaning |
|------|-------|---------|
| 🔴 | Critical | Immediate action required |
| 🟠 | High | Important, fix soon |
| 🟡 | Medium | Should be addressed |
| 🟢 | Low | Nice to fix |

## 🛠️ Manual Analysis

### Analyze a specific log file:

```bash
python3 scripts/ci-error-analyzer.py \
  --log-file path/to/workflow.log \
  --mode report \
  --output analysis.json
```

### Generate PR comment format:

```bash
python3 scripts/ci-error-analyzer.py \
  --log-file path/to/workflow.log \
  --mode comment
```

### Analyze from stdin:

```bash
cat workflow.log | python3 scripts/ci-error-analyzer.py --mode report
```

## ⚙️ Configuration

Edit `config/ci-error-analyzer.yaml`:

### Enable/Disable Features

```yaml
reporting:
  pr_comment_enabled: true      # Post to PR comments
  create_issues_for_critical: true  # Create issues for critical errors
  max_errors_in_report: 10      # Limit errors shown
```

### Customize Error Patterns

```yaml
custom_patterns:
  - pattern_id: "my_custom_error"
    category: "build_error"
    regex: "my.*error pattern"
    severity: "high"
    auto_fixable: false
```

## 🤖 Auto-Fix (Future)

Currently disabled for safety. When enabled:

```yaml
auto_fix:
  enabled: false
  allowed_categories:
    - lint_error
    - dependency_error
  require_approval: true
```

## 📝 Common Error Fixes

### Build Errors

**npm build failed**
```bash
npm install
npm run build
```

**TypeScript errors**
```bash
npm install --save-dev @types/[missing-package]
```

### Lint Errors

**ESLint errors**
```bash
npm run lint -- --fix
```

**Prettier formatting**
```bash
npm run format
```

### Dependency Errors

**Peer dependency conflict**
```bash
npm install --legacy-peer-deps
```

**Package not found**
```bash
npm install [package-name]
```

### Security Vulnerabilities

**npm audit issues**
```bash
npm audit fix
# or for major updates:
npm audit fix --force
```

## 🔗 Related Documentation

- Full Integration Guide: `docs/ci-error-analyzer-integration.md`
- CI Error Handler Module: `workspace/src/core/ci_error_handler/`
- Workflow Configuration: `.github/workflows/ci-error-analyzer.yml`
- Analyzer Configuration: `config/ci-error-analyzer.yaml`

## 💡 Tips

1. **Check PR comments** after failed workflows for quick insights
2. **Look for the 💡 icon** - it indicates auto-fix suggestions
3. **Critical issues** get their own GitHub issue - check Issues tab
4. **Fix auto-fixable errors first** - they're usually quick wins
5. **Review the full log** link in comments for complete context

## ❓ Troubleshooting

### Analyzer didn't run
- Verify the workflow failed (not cancelled)
- Check workflow triggers in `ci-error-analyzer.yml`
- Look for the workflow run in the Actions tab

### No PR comment posted
- Ensure the workflow is associated with a PR
- Check repository permissions (pull-requests: write)
- Review the analyzer workflow logs

### Wrong errors detected
- Add custom patterns in `config/ci-error-analyzer.yaml`
- Report false positives to improve detection

## 🆘 Need Help?

1. Check the full documentation: `docs/ci-error-analyzer-integration.md`
2. Review analyzer logs in GitHub Actions
3. Look at the analyzer workflow: `.github/workflows/ci-error-analyzer.yml`
4. Create an issue with the `ci-analyzer` label

---

**Last Updated**: 2026-01-09  
**Version**: 1.0.0
