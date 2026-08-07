# 專案套件優化與 Django 升級紀錄

這份文件紀錄專案進行套件整理（使用 `deptry`）以及升級 Python / Django 版本的完整流程與指令。

---

## 一、 使用 `deptry` 檢測並清理未使用的套件

### 1. 執行依賴檢查
若環境中未安裝 `deptry`，可以使用以下幾種方式執行：
```bash
# 方式 A：免安裝直接執行
uv run --with deptry deptry .

# 方式 B：新增至開發依賴後執行
uv add --dev deptry
uv run deptry .
```

---

### 2. 檢測結果與修正

#### 處理Package Name與Import Module Name不同問題
* **問題**：檢測顯示 `fitz` 被引用但未定義在 `pyproject.toml` 中，而 `pymupdf` 被標示為未使用。
* **原因**：`pymupdf` 套件在程式碼中是以 `import fitz` 方式匯入。
* **解決方案**：在 `pyproject.toml` 中新增設定：
  ```toml
  [tool.deptry.package_module_name_map]
  pymupdf = ["fitz"]
  ```

---

### 3. 套件移除與保留規劃

#### 確定可以直接移除
* `xlrd`：舊版 Excel 讀取套件。
* `beautifulsoup4`：HTML 解析套件。
* `lxml`：XML / HTML 解析套件。
* `urllib3`：HTTP 請求套件（已有 `requests` 或 Django 內建模組代替）。

**執行移除指令：**
```bash
uv remove xlrd beautifulsoup4 lxml urllib3
```

#### 暫時保留的套件
* `django-sslserver`：保留
* `waitress`：保留
* `whitenoise`：保留

#### 驗證
移除後執行 Django 檢查：
```bash
uv run python manage.py check
```
> [!NOTE]
> 執行 `uv run python manage.py check` 若完全正常，終端機將會顯示：
> `System check identified no issues (0 silenced).`

---

## 二、 升級 Python 與 Django 版本

### 1. 固定 Python 版本
升級 Python：
```bash
uv python pin 3.12
```

---

### 2. 更新 Django 版本
```bash
uv add "django>=5.2,<5.3"
```

---

### 3. 測試與檢查
升級後測試專案狀態：
```bash
uv run python manage.py check
```
> [!WARNING]
> **注意事項**：發現版本不同時，正規化方式已改變，請檢查資料庫 Migration 狀態：

```bash
uv run python manage.py makemigrations --dry-run
```

---

### 4. 自動升級與同步環境

1. **讓 `uv` 自動重新計算並升級所有套件至相容的最新版：**
   ```bash
   uv lock --upgrade
   ```

2. **將新版本同步到虛擬環境：**
   ```bash
   uv sync
   ```
