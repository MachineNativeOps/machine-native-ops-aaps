# CI/CD Error Analyzer Integration

## Overview

The CI/CD Error Analyzer automatically analyzes workflow failures, extracts structured error information, and provides actionable insights through PR comments and GitHub issues.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  CI/CD Workflow Execution                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                   (on failure)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│             CI Error Analyzer Workflow Triggered             │
│  (.github/workflows/ci-error-analyzer.yml)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Download Workflow Logs                      │
│  - Fetches logs from failed workflow runs                    │
│  - Combines logs from all failed jobs                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Run CI Error Analyzer Script                    │
│  (scripts/ci-error-analyzer.py)                              │
│                                                              │
│  Uses: workspace/src/core/ci_error_handler/                 │
│  - CIErrorAnalyzer: Parse and categorize errors              │
│  - ErrorPattern: Match known error patterns                  │
│  - Severity Classification: Critical/High/Medium/Low         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Analysis Results                            │
│  - Structured error data (JSON)                              │
│  - Error categorization                                      │
│  - Auto-fixable detection                                    │
│  - Fix suggestions                                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
            ┌───────────┴──────────┐
            │                      │
            ▼                      ▼
┌────────────────────┐  ┌────────────────────┐
│   PR Comment       │  │  GitHub Issue      │
│  (for all errors)  │  │ (critical errors)  │
└────────────────────┘  └────────────────────┘
```

## Components

### 1. CI Error Handler Module
**Location**: `workspace/src/core/ci_error_handler/`

Core Python modules for error analysis:
- `ci_error_analyzer.py` - Main analyzer with pattern matching
- `issue_manager.py` - GitHub issue creation and management
- `auto_fix_engine.py` - Auto-fix generation (future enhancement)
- `fix_status_tracker.py` - Track fix effectiveness

### 2. Analyzer Script
**Location**: `scripts/ci-error-analyzer.py`

Standalone script that:
- Reads workflow logs
- Analyzes errors using the CI Error Handler
- Generates reports in multiple formats (JSON, Markdown)
- Outputs to GitHub Actions environment

### 3. Analyzer Workflow
**Location**: `.github/workflows/ci-error-analyzer.yml`

Triggered automatically on workflow failures:
- Downloads logs from failed workflows
- Runs analyzer script
- Posts results to PR comments
- Creates issues for critical errors
- Uploads analysis artifacts

### 4. Configuration
**Location**: `config/ci-error-analyzer.yaml`

Settings for:
- Analysis behavior
- Reporting modes
- Auto-fix settings (disabled by default)
- Error category configuration
- Notification settings

## Features

### Automated Error Detection

The analyzer automatically detects and categorizes errors:

| Category | Examples | Severity | Auto-Fixable |
|----------|----------|----------|--------------|
| Build Error | npm build failed, compilation errors | High | No |
| Test Failure | Jest/Pytest failures | Medium | No |
| Lint Error | ESLint, Flake8 violations | Low | Yes |
| Type Error | TypeScript errors | High | No |
| Dependency Error | npm/pip resolution errors | Medium | Sometimes |
| Security Scan | npm audit, CodeQL alerts | High/Critical | Sometimes |
| Deployment Error | Docker, k8s errors | Critical | No |
| Timeout | Job timeout | Medium | No |
| Permission Error | EACCES, 403 errors | High | No |

### Intelligent Reporting

**PR Comments** (for all failures):
- Summary of all detected errors
- Categorization by type and severity
- Top 5-10 errors with details
- Fix suggestions when available
- Links to workflow runs

**GitHub Issues** (for critical errors only):
- Detailed error information
- Full context (workflow, commit, branch)
- Automatic labeling
- Direct links to logs

### Error Pattern Matching

The analyzer uses regex patterns to detect:
- Programming language-specific errors
- Build system errors
- Testing framework failures
- Security vulnerabilities
- Infrastructure issues

## Usage

### Automatic Triggering

The analyzer runs automatically when these workflows fail:
- `🚀 CI Pipeline` (ci.yml)
- `🤖 Autonomous CI Guardian` (autonomous-ci-guardian.yml)
- `🔒 Security Scan` (security.yml)

No manual intervention needed!

### Manual Analysis

Analyze a specific log file:

```bash
python3 scripts/ci-error-analyzer.py \
  --log-file path/to/workflow.log \
  --mode report \
  --output analysis.json
```

Generate PR comment format:

```bash
python3 scripts/ci-error-analyzer.py \
  --log-file path/to/workflow.log \
  --mode comment
```

### Configuration

Edit `config/ci-error-analyzer.yaml` to customize:

```yaml
analysis:
  enabled: true
  auto_analyze_failures: true
  max_log_size_mb: 50

reporting:
  mode: "comment"  # comment, issue, or both
  pr_comment_enabled: true
  create_issues_for_critical: true
  max_errors_in_report: 10

auto_fix:
  enabled: false  # For safety
  allowed_categories:
    - lint_error
    - dependency_error
```

## Integration Points

### Existing Workflows

The analyzer integrates with:
1. **CI Pipeline** (ci.yml) - Main quality checks
2. **Autonomous CI Guardian** (autonomous-ci-guardian.yml) - Predictive failure detection
3. **Security Scan** (security.yml) - Security vulnerability scanning

### Future Integrations

Planned enhancements:
- [ ] Integration with Auto-Fix Engine for safe auto-fixes
- [ ] ML-based error prediction
- [ ] Historical analysis and trending
- [ ] Integration with project management tools
- [ ] Slack/Discord notifications

## Error Categories Detail

### Build Errors
- npm/yarn build failures
- TypeScript compilation errors
- Python syntax errors
- Go build failures

**Example Detection**:
```regex
npm ERR!.*(?:build|compile).*failed
error TS\d+:.*
SyntaxError:.*
```

### Test Failures
- Jest test failures
- Pytest failures
- Go test failures
- Integration test failures

**Example Detection**:
```regex
FAIL.*\.test\.(js|ts|jsx|tsx)
FAILED.*test_.*\.py
```

### Lint Errors
- ESLint errors
- Prettier formatting issues
- Flake8/Black violations
- Type checking errors

**Example Detection**:
```regex
\d+:\d+\s+error\s+.*eslint
Prettier.*(?:error|failed)
.*\.py:\d+:\d+:.*[EWFC]\d+
```

### Dependency Errors
- npm peer dependency conflicts
- Python package not found
- Version conflicts
- Missing dependencies

**Example Detection**:
```regex
npm ERR!.*(?:peer dep|dependency|ERESOLVE)
(?:pip|ERROR).*(?:Could not find|No matching distribution)
```

### Security Vulnerabilities
- npm audit findings
- CodeQL alerts
- Dependency vulnerabilities
- Secret detection

**Example Detection**:
```regex
npm audit.*(?:high|critical)
CodeQL.*(?:alert|vulnerability|warning)
```

## Outputs

### JSON Report Structure

```json
{
  "errors": [
    {
      "error_id": "ERR-20260109-0001",
      "category": "build_error",
      "severity": "high",
      "title": "TypeScript compilation error",
      "message": "error TS2304: Cannot find name 'unknown'",
      "file_path": "src/index.ts",
      "line_number": 42,
      "column_number": 10,
      "auto_fixable": false,
      "fix_suggestion": "Check type definitions and imports"
    }
  ],
  "summary": {
    "total": 5,
    "by_category": {
      "build_error": 3,
      "lint_error": 2
    },
    "by_severity": {
      "high": 3,
      "low": 2
    },
    "auto_fixable_count": 2
  },
  "auto_fixable_errors": [ ... ]
}
```

### Markdown Report Example

```markdown
# 🔍 CI Error Analysis Report

## 📊 Summary
- **Total Errors**: 5
- **Auto-Fixable**: 2

### Errors by Category
- **build_error**: 3
- **lint_error**: 2

### Errors by Severity
- 🟠 **high**: 3
- 🟢 **low**: 2

## 🐛 Detected Errors

### 1. TypeScript compilation error
- **Category**: type_error
- **Severity**: high
- **Location**: `src/index.ts:42`

**Message**:
```
error TS2304: Cannot find name 'unknown'
```

💡 **Fix Suggestion**: Check type definitions and imports
```

## Permissions

The analyzer workflow requires:
- `contents: read` - Read repository code
- `issues: write` - Create issues for critical errors
- `pull-requests: write` - Post PR comments
- `actions: read` - Access workflow run data

## Troubleshooting

### Analyzer not running
- Check workflow triggers in `ci-error-analyzer.yml`
- Verify permissions are configured correctly
- Check if the referenced workflows exist

### No errors detected
- Verify log content is being downloaded
- Check custom error patterns in config
- Enable verbose mode for debugging

### PR comments not appearing
- Verify PR exists for the workflow run
- Check `GITHUB_TOKEN` permissions
- Review workflow logs for API errors

## Compliance

This integration aligns with:
- **AI Behavior Contract**: Binary response protocol (Section 2)
- **SynergyMesh Core**: Autonomous operation (Section 22)
- **INSTANT Execution**: Event-driven automation (Section 17)
- **Governance**: 30-agents framework compliance

## References

- CI Error Handler Module: `workspace/src/core/ci_error_handler/`
- Analyzer Script: `scripts/ci-error-analyzer.py`
- Configuration: `config/ci-error-analyzer.yaml`
- Workflow: `.github/workflows/ci-error-analyzer.yml`

---

**Status**: ✅ Active  
**Version**: 1.0.0  
**Last Updated**: 2026-01-09
