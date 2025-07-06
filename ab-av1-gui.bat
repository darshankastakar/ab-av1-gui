@echo off
set VENV_DIR=venv

echo Checking for virtual environment...
if not exist "%VENV_DIR%" (
    echo Creating virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b %errorlevel%
    )
)

echo Activating virtual environment and installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo Starting the application...
python gui.py

echo.
echo Application closed.
