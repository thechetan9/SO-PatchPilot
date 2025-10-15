# PatchPilot Quick Start Script for Windows PowerShell
# Run this script to set up PatchPilot in one go

Write-Host "================================" -ForegroundColor Cyan
Write-Host "PatchPilot Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Step 1: Check Python
Write-Host "`n[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Write-Host "`n[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate virtual environment
Write-Host "`n[3/6] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Step 4: Install dependencies
Write-Host "`n[4/6] Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 5: Check AWS credentials
Write-Host "`n[5/6] Checking AWS credentials..." -ForegroundColor Yellow
if ($env:AWS_ACCESS_KEY_ID) {
    Write-Host "✓ AWS credentials found" -ForegroundColor Green
} else {
    Write-Host "⚠ AWS credentials not set" -ForegroundColor Yellow
    Write-Host "  Set them with:" -ForegroundColor Yellow
    Write-Host "  `$env:AWS_ACCESS_KEY_ID = 'your_key'" -ForegroundColor Gray
    Write-Host "  `$env:AWS_SECRET_ACCESS_KEY = 'your_secret'" -ForegroundColor Gray
    Write-Host "  `$env:AWS_SESSION_TOKEN = 'your_token'" -ForegroundColor Gray
    Write-Host "  `$env:AWS_REGION = 'us-east-2'" -ForegroundColor Gray
}

# Step 6: Run tests
Write-Host "`n[6/6] Running tests..." -ForegroundColor Yellow
pytest tests/ -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All tests passed" -ForegroundColor Green
} else {
    Write-Host "⚠ Some tests failed" -ForegroundColor Yellow
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Set AWS credentials (if not already set)" -ForegroundColor Gray
Write-Host "2. Run the demo: python demo.py" -ForegroundColor Gray
Write-Host "3. Start the API: python -m src.api" -ForegroundColor Gray
Write-Host "4. Read SETUP_GUIDE.md for detailed instructions" -ForegroundColor Gray

Write-Host "`nVirtual environment is active. Happy coding! 🚀" -ForegroundColor Green

