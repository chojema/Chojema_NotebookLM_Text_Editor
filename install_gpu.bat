@echo off
chcp 65001 > nul
echo ===================================================
echo   Chojema Text Editor - GPU Setup (NVIDIA Only)
echo ===================================================

if not exist "venv" (
    echo [오류] 먼저 'run.bat'을 한 번 실행하여 기본 환경을 구성해주세요.
    pause
    exit /b
)

echo [알림] 가상 환경에 진입합니다...
call venv\Scripts\activate

echo.
echo [알림] 기존에 설치된 CPU 버전의 PyTorch를 제거합니다...
pip uninstall -y torch torchvision torchaudio

echo.
echo [알림] GPU 가속을 지원하는 PyTorch (CUDA 12.1) 버전을 설치합니다.
echo *** 파일 크기가 약 2.5GB ~ 3GB 정도 되므로 시간이 걸릴 수 있습니다. ***
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo ===================================================
echo [완료] GPU 설정이 완료되었습니다!
echo 이제 'run.bat'을 실행하면 자동으로 GPU를 사용하여 더 빠르게 작동합니다.
echo ===================================================
pause
