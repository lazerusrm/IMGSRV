# PowerShell Auto-Installer for Image Sequence Server (Windows)
# This script sets up the development environment on Windows

Write-Host "🚀 Image Sequence Server - Windows Development Setup" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Blue

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script requires administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing Chocolatey package manager..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Install Python and Git
Write-Host "🐍 Installing Python and Git..." -ForegroundColor Yellow
choco install -y python git

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Python dependencies
Write-Host "📚 Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create virtual environment
Write-Host "🔧 Setting up virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies in venv
pip install -r requirements.txt

# Test basic functionality
Write-Host "🧪 Testing basic functionality..." -ForegroundColor Yellow
python test_basic.py

Write-Host ""
Write-Host "✅ Windows development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Blue
Write-Host "1. Activate virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run the application: python main.py" -ForegroundColor White
Write-Host "3. Test camera connectivity (requires Linux/ONVIF camera)" -ForegroundColor White
Write-Host ""
Write-Host "🌐 For production deployment, use Linux with the autoinstall.sh script" -ForegroundColor Yellow
