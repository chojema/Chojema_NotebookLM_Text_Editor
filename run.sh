#!/bin/bash

echo "==================================================="
echo "  Chojema NotebookLM Text Editor (Mac/Linux)"
echo "==================================================="

# 1. 가상환경 없으면 생성
if [ ! -d "venv" ]; then
    echo "[초기 설정] 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 설치 여부 확인
if [ -f "venv/installed.flag" ]; then
    echo "[확인] 바로 실행합니다!"
else
    # 4. 패키지 설치 (최초 1회만)
    echo "[설치] 필요한 라이브러리를 설치합니다..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 설치 완료 도장 찍기
    touch venv/installed.flag
fi

# 5. 앱 실행
echo "[실행] 브라우저를 엽니다..."
streamlit run app.py