@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🚀 Starting git update process...

REM Get current directory
set CURRENT_DIR=%CD%
echo 📍 Current directory: %CURRENT_DIR%

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Error: Not a git repository. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check git status
echo 📊 Checking git status...
git status --porcelain

REM Check if there are any changes to commit
git status --porcelain > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="" (
    echo ℹ️  No changes to commit. Repository is clean.
    pause
    exit /b 0
)

REM Remove any files that should be ignored but are still tracked
echo 🧹 Cleaning up ignored files...
if exist "update.sh" (
    git rm --cached "update.sh" 2>nul
)
if exist "_cursor" (
    git rm --cached -r "_cursor" 2>nul
)
if exist "TXT" (
    git rm --cached -r "TXT" 2>nul
)
if exist ".venv" (
    git rm --cached -r ".venv" 2>nul
)
if exist "git_update.sh" (
    git rm --cached "git_update.sh" 2>nul
)
if exist "git_update.ps1" (
    git rm --cached "git_update.ps1" 2>nul
)
if exist "git_update.bat" (
    git rm --cached "git_update.bat" 2>nul
)
if exist "porn.sh" (
    git rm --cached "porn.sh" 2>nul
)
if exist "porn.py" (
    git rm --cached "porn.py" 2>nul
)
if exist "porn_req.txt" (
    git rm --cached "porn_req.txt" 2>nul
)
if exist "cleanup_git.sh" (
    git rm --cached "cleanup_git.sh" 2>nul
)
if exist "cleanup_git.ps1" (
    git rm --cached "cleanup_git.ps1" 2>nul
)

REM Add all changes
echo ➕ Adding all changes...
git add .

REM Check if add was successful
if errorlevel 1 (
    echo ❌ Error: Failed to add changes to git
    pause
    exit /b 1
)

REM Commit changes
echo 💾 Committing changes...
git commit -m "update code"

REM Check if commit was successful
if errorlevel 1 (
    echo ❌ Error: Failed to commit changes
    pause
    exit /b 1
)

REM Force push to newdesign branch
echo 🚀 Force pushing to newdesign branch...
git push origin newdesign --force

REM Check if push was successful
if errorlevel 1 (
    echo ❌ Error: Failed to push to newdesign branch
    pause
    exit /b 1
)

echo ✅ Git update completed successfully!

REM Show last commit info
for /f "tokens=*" %%i in ('git log -1 --format^=%%H - %%s ^(%%cr^)') do set LAST_COMMIT=%%i
echo 📅 Last commit: %LAST_COMMIT%

pause
