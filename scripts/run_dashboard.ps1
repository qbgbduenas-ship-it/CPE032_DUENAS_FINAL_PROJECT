Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment not found. Follow README.md setup first."
    exit 1
}
.\.venv\Scripts\Activate.ps1
streamlit run app.py
