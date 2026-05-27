@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%ROOT%mineintel-research\scripts\start_progress_ui.py" --task "MineIntel 演示控制台"
  exit /b
)
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%ROOT%mineintel-research\scripts\start_progress_ui.py" --task "MineIntel 演示控制台"
  exit /b
)
start "" "%ROOT%demo-ui\index.html"
