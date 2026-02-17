@echo off
chcp 65001 > nul
echo ===================================================
echo   Chojema NotebookLM Text Editor (Windows)
echo ===================================================

:: 1. 가상환경이 없으면 생성
if not exist "venv" (
    echo [초기 설정] 가상환경을 생성합니다...
    python -m venv venv
)

:: 2. 가상환경 진입
call venv\Scripts\activate

:: 3. 설치 여부 확인 (도장이 있으면 건너뜀)
if exist "venv\installed.flag" (
    echo [확인] 바로 실행합니다!
    goto :RUN_APP
)

:: 4. 패키지 설치 (최초 1회만)
echo [설치] 필요한 AI 도구를 설치합니다... (잠시만 기다려주세요)
pip install -r requirements.txt

:: 설치 완료 도장 찍기
echo installed > venv\installed.flag

:RUN_APP
:: 5. 앱 실행
echo [실행] 브라우저를 엽니다...
streamlit run app.py

pause