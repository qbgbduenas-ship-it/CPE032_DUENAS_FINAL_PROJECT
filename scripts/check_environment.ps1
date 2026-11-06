Write-Host "=== Python ==="
python --version
Write-Host "`n=== Java ==="
java -version
Write-Host "`n=== Project files ==="
Get-ChildItem -Force
Write-Host "`n=== Environment ==="
python -c "import sys; print(sys.executable)"
