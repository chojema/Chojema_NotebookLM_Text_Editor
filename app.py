import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pypdfium2 as pdfium
import logic
import io

# 페이지 설정
st.set_page_config(page_title="Chojema Editor", layout="wide")

st.title("🎨 Chojema NotebookLM Text Editor")
st.markdown("PDF나 이미지를 드래그하고, 지우고 싶은 **텍스트 영역을 박스로 선택**하세요.")

# --- 사이드바: 파일 업로드 ---
st.sidebar.header("📂 파일 열기")
uploaded_file = st.sidebar.file_uploader("파일 업로드 (PDF/JPG/PNG)", type=["png", "jpg", "jpeg", "pdf"])

# 세션 상태 초기화
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""

# 파일 로드 로직
if uploaded_file:
    # 1. PDF 처리 (pypdfium2 사용 - Poppler 불필요)
    if uploaded_file.type == "application/pdf":
        try:
            pdf = pdfium.PdfDocument(uploaded_file)
            n_pages = len(pdf)
            
            st.sidebar.subheader(f"총 {n_pages} 페이지")
            page_idx = st.sidebar.number_input("페이지 이동", min_value=1, max_value=n_pages, value=1) - 1
            
            # 페이지 렌더링 키 생성
            current_file_id = f"{uploaded_file.name}_page_{page_idx}"
            
            if st.session_state.get('last_uploaded') != current_file_id:
                page = pdf[page_idx]
                # scale=2: 고해상도 렌더링
                bitmap = page.render(scale=2)
                pil_image = bitmap.to_pil()
                
                st.session_state.current_image = pil_image
                st.session_state.last_uploaded = current_file_id
                st.session_state.canvas_key += 1 # 캔버스 리셋
                st.session_state.extracted_text = "" # 텍스트 리셋
                
        except Exception as e:
            st.error(f"PDF를 읽는 중 오류가 발생했습니다: {e}")
            
    # 2. 이미지 처리
    else:
        if st.session_state.get('last_uploaded') != uploaded_file.name:
            image = Image.open(uploaded_file).convert("RGB")
            st.session_state.current_image = image
            st.session_state.last_uploaded = uploaded_file.name
            st.session_state.canvas_key += 1
            st.session_state.extracted_text = ""

# --- 메인 작업 공간 ---
if st.session_state.current_image:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("편집 캔버스")
        # 캔버스 높이 자동 조절 (비율 유지)
        img_w, img_h = st.session_state.current_image.size
        canvas_height = 600
        canvas_width = int(img_w * (canvas_height / img_h)) if img_h > 0 else 800
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # 선택 영역 색상 (반투명 주황)
            stroke_width=2,
            stroke_color="#000000",
            background_image=st.session_state.current_image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="rect", # 사각형 그리기 모드 고정
            key=f"canvas_{st.session_state.canvas_key}",
        )

    with col2:
        st.subheader("🛠️ 도구")
        
        # 선택된 영역이 있는지 확인
        if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
            objects = canvas_result.json_data["objects"]
            last_object = objects[-1] # 가장 최근에 그린 박스
            
            if last_object["type"] == "rect":
                st.info("영역이 선택되었습니다.")
                
                if st.button("✨ 텍스트 지우기 & 복원", type="primary"):
                    with st.spinner("AI가 텍스트를 읽고 배경을 복원 중입니다..."):
                        # 로직 호출
                        clean_image, text = logic.process_selected_area(
                            st.session_state.current_image, 
                            last_object
                        )
                        
                        # 결과 저장 및 갱신
                        st.session_state.current_image = clean_image
                        st.session_state.extracted_text = text
                        st.session_state.canvas_key += 1
                        st.rerun()

        # 추출된 텍스트 표시 및 편집
        if st.session_state.extracted_text:
            st.success("작업 완료!")
            st.text_area("추출된 텍스트 내용", value=st.session_state.extracted_text, height=150)
            
            # 다운로드 버튼
            buf = io.BytesIO()
            st.session_state.current_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 현재 이미지 다운로드",
                data=byte_im,
                file_name="edited_image.png",
                mime="image/png"
            )

else:
    st.info("👈 왼쪽 사이드바에 파일을 드래그해서 넣어주세요.")