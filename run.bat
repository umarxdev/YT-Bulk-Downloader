@echo off
echo Installing/upgrading pip and installing requirements (this may take a moment)...
REM Use the same Python interpreter to install packages
python -m pip install --upgrade pip setuptools wheel --disable-pip-version-check -q
if errorlevel 1 (
  echo Warning: pip upgrade had an issue, continuing...
)

REM Install requirements quietly; use script folder path (%~dp0) to find requirements.txt
python -m pip install -r "%~dp0requirements.txt" --disable-pip-version-check -q
if errorlevel 1 (
  echo Quiet install failed. Retrying with verbose output...
  python -m pip install -r "%~dp0requirements.txt"
)

echo Starting YouTube Bulk Downloader...
python "%~dp0main.py"
pause
