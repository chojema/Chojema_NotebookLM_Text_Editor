# -*- coding: utf-8 -*-
import base64
import io
import os
from datetime import datetime

# Disable MKLDNN default in PaddleX/Paddle runtime for stability.
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"

import pypdfium2 as pdfium
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

import logic

st.set_page_config(page_title="Chojema Text Editor", layout="wide")

I18N = {
    "ko": {
        "lang_label": "언어 선택",
        "workspace": "파일 불러오기",
        "title": "Chojema NotebookLM Text Editor",
        "subtitle": "이미지 영역에서 필요한 부분을 마우스 끌어 선택한 후 우측 메뉴에서 필요한 기능을 선택합니다.",
        "upload": "NotebookLM 등으로 작성한 인포그래픽이나 발표용 PDF, JPG, PNG 등을 불러옵니다.",
        "reset": "작업 초기화",
        "pdf_page": "PDF 페이지",
        "pdf_pages": "전체 페이지",
        "go_last_page": "마지막 페이지로 가기",
        "go_first_page": "첫 페이지로 가기",
        "page_status": "페이지 {current}/{total}",
        "page_button": "{page}페이지",
        "empty_start": "왼쪽 사이드바에서 PDF 또는 이미지를 업로드해 시작하세요.",
        "zoom_minus": "축소",
        "zoom_plus": "확대",
        "undo": "되돌리기",
        "clear_selection": "선택 영역 취소",
        "actions": "작업",
        "selection_ready": "선택 영역 준비 완료",
        "select_first": "먼저 캔버스에서 영역을 선택하세요.",
        "remove_text": "텍스트 추출 후 배경 복원",
        "extract_only": "텍스트만 추출",
        "restore_bg": "텍스트 추출 없이 배경 복원",
        "spinner_remove": "OCR + 인페인팅 처리 중...",
        "spinner_extract": "OCR 처리 중...",
        "spinner_restore": "OCR 없이 배경 복원 중...",
        "no_text": "(감지된 텍스트 없음)",
        "restore_done": "(배경 복원 완료: OCR 미실행)",
        "copy_text": "텍스트 복사",
        "copy_text_done": "복사됨",
        "copy_text_fail": "복사 실패",
        "text_box_placeholder": "추출된 텍스트가 여기에 저장됩니다.",
        "download": "현재 이미지 다운로드",
        "copy_clipboard": "현재 이미지를 클립보드에 복사",
        "copied": "복사됨",
        "copy_failed": "복사 실패 (HTTPS 필요)",
        "extracted_text": "추출 텍스트",
        "ocr_result": "OCR 결과",
        "ocr_placeholder": "선택 영역의 OCR 결과가 여기에 표시됩니다.",
    },
    "en": {
        "lang_label": "Language selector",
        "workspace": "Load Files",
        "title": "Chojema NotebookLM Text Editor",
        "subtitle": "Drag to select the required area in the image, then choose the needed function from the menu on the right.",
        "upload": "Load infographics or presentation files created with NotebookLM, including PDF, JPG, and PNG.",
        "reset": "Reset Workspace",
        "pdf_page": "PDF page",
        "pdf_pages": "All Pages",
        "go_last_page": "Go to Last Page",
        "go_first_page": "Go to First Page",
        "page_status": "Page {current}/{total}",
        "page_button": "Page {page}",
        "empty_start": "Upload a PDF or image from the left sidebar to start.",
        "zoom_minus": "Zoom -",
        "zoom_plus": "Zoom +",
        "undo": "Undo",
        "clear_selection": "Clear Selection",
        "actions": "Actions",
        "selection_ready": "Selection ready",
        "select_first": "Select a region on the canvas first.",
        "remove_text": "Extract Text + Rebuild Background",
        "extract_only": "Extract Text Only",
        "restore_bg": "Rebuild Background without Text Extraction",
        "spinner_remove": "Running OCR + inpainting...",
        "spinner_extract": "Running OCR...",
        "spinner_restore": "Running inpainting without OCR...",
        "no_text": "(No text detected)",
        "restore_done": "(Background rebuilt: OCR skipped)",
        "copy_text": "Copy Text",
        "copy_text_done": "Copied",
        "copy_text_fail": "Copy failed",
        "text_box_placeholder": "Extracted text will be saved here.",
        "download": "Download Current Image",
        "copy_clipboard": "Copy Current Image to Clipboard",
        "copied": "Copied",
        "copy_failed": "Clipboard copy failed (HTTPS required)",
        "extracted_text": "Extracted Text",
        "ocr_result": "OCR result",
        "ocr_placeholder": "Text extracted from selected region will appear here.",
    },
}


st.markdown(
    """
<style>
:root {
  --bg-0: #f6f7fb;
  --bg-1: #ffffff;
  --ink-0: #101323;
  --ink-1: #5e6473;
  --line-0: #d8dce8;
  --accent-0: #0f766e;
  --accent-1: #0b4f4a;
}
.stApp {
  background:
    radial-gradient(1200px 600px at 8% -10%, #d9eef2 0%, transparent 55%),
    radial-gradient(1000px 500px at 100% 0%, #eef0ff 0%, transparent 50%),
    var(--bg-0);
}
[data-testid="stAppViewContainer"] .main .block-container {
  padding-top: 0 !important;
}
h1 {
  margin-top: -0.35rem !important;
  margin-bottom: 0.35rem !important;
}
p {
  margin-top: 0.15rem !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  margin-top: 10px !important;
}
h1, h2, h3, p, label, span, div {
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f9 100%);
  border-right: 1px solid var(--line-0);
}
[class*="st-key-canvas_"] {
  overflow: auto !important;
  max-height: 73vh !important;
  width: 100% !important;
  max-width: 100% !important;
  border: 1px solid var(--line-0) !important;
  border-radius: 12px !important;
  background: var(--bg-1) !important;
  box-shadow: 0 8px 28px rgba(16, 19, 35, 0.07) !important;
}
[class*="st-key-canvas_"] iframe {
  display: block !important;
  max-width: none !important;
}
[class*="st-key-canvas_"] > div {
  width: max-content !important;
  min-width: 100% !important;
  max-width: none !important;
  overflow: auto !important;
}
[class*="st-key-canvas_"] div:has(> button[title="Send to Streamlit"]),
[class*="st-key-canvas_"] div:has(> button[title="Clear"]) {
  display: none !important;
}
.caption-pill {
  display: inline-block;
  background: #e6f4f1;
  color: var(--accent-1);
  border: 1px solid #b9e1da;
  border-radius: 999px;
  font-size: 12px;
  padding: 4px 10px;
  margin-top: 6px;
}
.sidebar-footer {
  position: fixed;
  bottom: 12px;
  left: 0;
  width: 18rem;
  text-align: center;
  font-size: 12px;
  color: #6f7482;
}
.right-panel-top {
  margin-top: -14px;
}
.status-pill {
  display: inline-block;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
  padding: 7px 12px;
  border-radius: 999px;
  margin-bottom: 8px;
}
.status-pill.ok {
  color: #0b4f4a;
  background: #e6f4f1;
  border: 1px solid #b9e1da;
}
.status-pill.info {
  color: #253046;
  background: #edf2fa;
  border: 1px solid #bdcbe6;
}
</style>
""",
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "current_image": None,
        "canvas_key": 0,
        "extracted_text": "",
        "zoom_level": 1.0,
        "uploader_key": 0,
        "original_stem": "image",
        "current_page_idx": None,
        "pdf_page_idx": 0,
        "last_uploaded_token": None,
        "history_stack": [],
        "extracted_history": ["", "", ""],
        "current_selection": None,
        "lang": "ko",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def t(key: str) -> str:
    lang = st.session_state.get("lang", "ko")
    return I18N.get(lang, I18N["ko"]).get(key, key)


def reset_workspace():
    current_lang = st.session_state.get("lang", "ko")
    next_uploader_key = st.session_state.get("uploader_key", 0) + 1
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.uploader_key = next_uploader_key
    st.session_state.lang = current_lang
    st.rerun()


def push_history(image: Image.Image):
    stack = st.session_state.history_stack
    stack.append(image.copy())
    st.session_state.history_stack = stack[-8:]


def pop_history():
    stack = st.session_state.history_stack
    if stack:
        st.session_state.current_image = stack.pop()
        st.session_state.history_stack = stack
        st.session_state.canvas_key += 1
        st.session_state.extracted_text = ""
        st.rerun()


def push_extracted_text(text: str):
    history = st.session_state.get("extracted_history", ["", "", ""])
    new_text = (text or "").strip()
    if not new_text:
        return
    updated = [new_text, history[0], history[1]]
    st.session_state.extracted_history = updated
    for idx, value in enumerate(updated):
        st.session_state[f"text_history_{idx}"] = value


def current_download_name():
    stem = st.session_state.get("original_stem", "image")
    page_idx = st.session_state.get("current_page_idx", None)
    if page_idx is None:
        return f"{stem}_edited.png"
    return f"{stem}_edited_{page_idx + 1:02d}.png"


def current_image_bytes():
    buf = io.BytesIO()
    st.session_state.current_image.save(buf, format="PNG")
    return buf.getvalue()


def extract_selection(canvas_json, img_w, img_h, canvas_w, canvas_h):
    if not canvas_json:
        return None
    objects = canvas_json.get("objects", [])
    if not objects:
        return None

    rect = None
    for obj in reversed(objects):
        if obj.get("type") == "rect":
            rect = obj
            break
    if rect is None:
        return None

    scale_x = img_w / canvas_w
    scale_y = img_h / canvas_h
    return {
        "left": rect["left"] * scale_x,
        "top": rect["top"] * scale_y,
        "width": rect["width"] * scale_x,
        "height": rect["height"] * scale_y,
    }


def selection_to_canvas_rect(selection, img_w, img_h, canvas_w, canvas_h):
    if not selection:
        return None
    return {
        "type": "rect",
        "left": selection["left"] * (canvas_w / img_w),
        "top": selection["top"] * (canvas_h / img_h),
        "width": selection["width"] * (canvas_w / img_w),
        "height": selection["height"] * (canvas_h / img_h),
        "fill": "rgba(15, 118, 110, 0.20)",
        "stroke": "#0f766e",
        "strokeWidth": 2,
    }


def rect_to_selection(rect, img_w, img_h, canvas_w, canvas_h):
    scale_x = img_w / canvas_w
    scale_y = img_h / canvas_h
    left = rect["left"] * scale_x
    top = rect["top"] * scale_y
    width = rect["width"] * scale_x
    height = rect["height"] * scale_y
    left = max(0.0, min(float(img_w), left))
    top = max(0.0, min(float(img_h), top))
    width = max(1.0, min(float(img_w) - left, width))
    height = max(1.0, min(float(img_h) - top, height))
    return {"left": left, "top": top, "width": width, "height": height}


@st.cache_data(show_spinner=False)
def pdf_page_count(pdf_bytes):
    return len(pdfium.PdfDocument(pdf_bytes))


@st.cache_data(show_spinner=False)
def pdf_page_image(pdf_bytes, page_idx, scale=2.0):
    pdf = pdfium.PdfDocument(pdf_bytes)
    pil_image = pdf[page_idx].render(scale=scale).to_pil().convert("RGB")
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def pdf_thumbnails(pdf_bytes, thumb_scale=0.23):
    pdf = pdfium.PdfDocument(pdf_bytes)
    thumbs = []
    for idx in range(len(pdf)):
        thumb = pdf[idx].render(scale=thumb_scale).to_pil().convert("RGB")
        buf = io.BytesIO()
        thumb.save(buf, format="PNG")
        thumbs.append(buf.getvalue())
    return thumbs


init_state()

lang_choice = st.sidebar.radio(
    t("lang_label"),
    options=["한국어", "English"],
    index=0 if st.session_state.lang == "ko" else 1,
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state.lang = "ko" if lang_choice == "한국어" else "en"

st.markdown(
    """
<style>
[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed #0f766e !important;
  border-radius: 12px !important;
  background: #eef8f6 !important;
  box-shadow: inset 0 0 0 1px #c8e9e3 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

if st.session_state.lang == "ko":
    st.markdown(
        """
<style>
[data-testid="stFileUploaderDropzoneInstructions"] > div {
  display: none !important;
}
[data-testid="stFileUploaderDropzone"]::before {
  content: "여기에 파일을 끌어놓거나";
  display: block;
  text-align: center;
  color: #1f2937;
  font-size: 14px;
  margin-bottom: 6px;
}
[data-testid="stFileUploaderDropzone"] button {
  font-size: 0 !important;
}
[data-testid="stFileUploaderDropzone"] button::after {
  content: "파일 선택";
  font-size: 14px;
}
</style>
""",
        unsafe_allow_html=True,
    )

st.title(t("title"))
st.markdown(t("subtitle"))

st.sidebar.header(t("workspace"))
uploaded_file = st.sidebar.file_uploader(
    t("upload"),
    type=["pdf", "png", "jpg", "jpeg"],
    key=f"uploader_{st.session_state.uploader_key}",
)

if st.sidebar.button(t("reset"), use_container_width=True):
    reset_workspace()

selected_page_idx = None
if uploaded_file and uploaded_file.type == "application/pdf":
    pdf_bytes = uploaded_file.getvalue()
    total_pages = pdf_page_count(pdf_bytes)
    base_pdf_token = f"{uploaded_file.name}:{uploaded_file.size}:pdf"

    if st.session_state.get("last_uploaded_pdf_token") != base_pdf_token:
        st.session_state.pdf_page_idx = 0
        st.session_state.last_uploaded_pdf_token = base_pdf_token

    if st.sidebar.button(t("go_last_page"), use_container_width=True, key=f"{base_pdf_token}_go_last"):
        st.session_state.pdf_page_idx = total_pages - 1
        st.rerun()

    selected_page_idx = max(0, min(total_pages - 1, st.session_state.pdf_page_idx))
    st.sidebar.caption(t("page_status").format(current=selected_page_idx + 1, total=total_pages))

    st.sidebar.markdown(f"**{t('pdf_pages')}**")
    thumbs = pdf_thumbnails(pdf_bytes)
    st.sidebar.markdown(
        '<style>[class*="st-key-pdfthumb"]{height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;}</style>',
        unsafe_allow_html=True,
    )
    for idx, thumb_bytes in enumerate(thumbs):
        is_selected = idx == selected_page_idx
        border = "3px solid #0f766e" if is_selected else "2px solid #d8dce8"
        bg = "#e6f4f1" if is_selected else "#ffffff"
        weight = "700" if is_selected else "400"
        b64_thumb = base64.b64encode(thumb_bytes).decode()
        thumb_pil = Image.open(io.BytesIO(thumb_bytes))
        tw, th = thumb_pil.size
        iframe_h = int(280 * th / tw) + 48
        thumb_html = (
            f'<style>body{{margin:0;padding:0;}}</style>'
            f'<div onclick="var b=window.parent.document.querySelector(\'.st-key-pdfthumb{idx} button\');if(b)b.click();"'
            f' style="cursor:pointer;border:{border};border-radius:8px;padding:4px;'
            f'background:{bg};text-align:center;">'
            f'<img src="data:image/png;base64,{b64_thumb}" style="width:100%;border-radius:4px;"/>'
            f'<div style="font-size:12px;color:#5e6473;margin-top:2px;font-weight:{weight};">'
            f'{idx + 1}/{total_pages}</div></div>'
        )
        with st.sidebar:
            st.components.v1.html(thumb_html, height=iframe_h)
        if st.sidebar.button("go", key=f"pdfthumb{idx}"):
            st.session_state.pdf_page_idx = idx
            st.rerun()
    if st.sidebar.button(t("go_first_page"), use_container_width=True, key=f"{base_pdf_token}_go_first"):
        st.session_state.pdf_page_idx = 0
        st.rerun()

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_bytes = uploaded_file.getvalue()
        file_token = f"{uploaded_file.name}:{uploaded_file.size}:pdf:{selected_page_idx}"
        if st.session_state.last_uploaded_token != file_token:
            pil_image = Image.open(io.BytesIO(pdf_page_image(pdf_bytes, selected_page_idx, scale=2.0))).convert("RGB")
            st.session_state.current_image = pil_image
            st.session_state.last_uploaded_token = file_token
            st.session_state.original_stem = os.path.splitext(uploaded_file.name)[0]
            st.session_state.current_page_idx = selected_page_idx
            st.session_state.canvas_key += 1
            st.session_state.extracted_text = ""
            st.session_state.zoom_level = 1.0
            st.session_state.history_stack = []
            st.session_state.current_selection = None
    else:
        file_token = f"{uploaded_file.name}:{uploaded_file.size}:img"
        if st.session_state.last_uploaded_token != file_token:
            pil_image = Image.open(uploaded_file).convert("RGB")
            st.session_state.current_image = pil_image
            st.session_state.last_uploaded_token = file_token
            st.session_state.original_stem = os.path.splitext(uploaded_file.name)[0]
            st.session_state.current_page_idx = None
            st.session_state.canvas_key += 1
            st.session_state.extracted_text = ""
            st.session_state.zoom_level = 1.0
            st.session_state.history_stack = []
            st.session_state.current_selection = None

current_year = datetime.now().year
st.sidebar.markdown(
    f"""
<div class="sidebar-footer">
  Chulwoo Park, {current_year}<br/>
  <a href="https://cantips.com" target="_blank">Blog</a> |
  <a href="https://www.youtube.com/@cantips" target="_blank">YouTube</a>
</div>
""",
    unsafe_allow_html=True,
)

if not st.session_state.current_image:
    st.info(t("empty_start"))
    st.stop()

canvas_col, panel_col = st.columns([5, 1.2])
img_w, img_h = st.session_state.current_image.size
base_canvas_width = 760
viewport_canvas_width = base_canvas_width
viewport_canvas_height = int(img_h * (viewport_canvas_width / img_w)) if img_w > 0 else 600
canvas_width = int(viewport_canvas_width * st.session_state.zoom_level)
canvas_height = int(viewport_canvas_height * st.session_state.zoom_level)

with canvas_col:
    tool_col1, tool_col2, tool_col3, tool_col4, tool_col5, tool_col6 = st.columns([1, 2, 1, 1, 1, 1.2])
    with tool_col1:
        if st.button(t("zoom_minus"), use_container_width=True):
            st.session_state.zoom_level = max(0.25, round(st.session_state.zoom_level - 0.25, 2))
            st.session_state.canvas_key += 1
            st.rerun()
    with tool_col2:
        zoom_percent = int(st.session_state.zoom_level * 100)
        selected_zoom = st.slider(
            "Zoom",
            min_value=25,
            max_value=400,
            step=25,
            value=zoom_percent,
            label_visibility="collapsed",
        )
        if selected_zoom != zoom_percent:
            st.session_state.zoom_level = selected_zoom / 100
            st.session_state.canvas_key += 1
            st.rerun()
    with tool_col3:
        if st.button(t("zoom_plus"), use_container_width=True):
            st.session_state.zoom_level = min(4.0, round(st.session_state.zoom_level + 0.25, 2))
            st.session_state.canvas_key += 1
            st.rerun()
    with tool_col4:
        if st.button("100%", use_container_width=True):
            st.session_state.zoom_level = 1.0
            st.session_state.canvas_key += 1
            st.rerun()
    with tool_col5:
        if st.button(t("undo"), use_container_width=True, disabled=not st.session_state.history_stack):
            pop_history()
    with tool_col6:
        if st.button(t("clear_selection"), use_container_width=True):
            st.session_state.current_selection = None
            st.session_state.canvas_key += 1
            st.rerun()

    current_rect = selection_to_canvas_rect(
        st.session_state.current_selection,
        img_w=img_w,
        img_h=img_h,
        canvas_w=canvas_width,
        canvas_h=canvas_height,
    )
    initial_drawing = {"version": "4.4.0", "objects": [current_rect]} if current_rect else None

    canvas_result = st_canvas(
        fill_color="rgba(15, 118, 110, 0.20)",
        stroke_width=2,
        stroke_color="#0f766e",
        background_image=st.session_state.current_image,
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode="rect",
        display_toolbar=False,
        initial_drawing=initial_drawing,
        key=f"canvas_{st.session_state.canvas_key}",
    )
    st.components.v1.html(
        f"""
<script>
(function() {{
  var w = {canvas_width};
  var h = {canvas_height};
  function forceScrollableCanvas() {{
    var doc = window.parent.document;
    var wrap = doc.querySelector('[class*="st-key-canvas_"]');
    var iframe = doc.querySelector('iframe[title="streamlit_drawable_canvas.st_canvas"]');
    if (!wrap || !iframe) return;

    wrap.style.setProperty('overflow-x', 'auto', 'important');
    wrap.style.setProperty('overflow-y', 'auto', 'important');
    wrap.style.setProperty('max-width', '100%', 'important');

    if (wrap.firstElementChild) {{
      wrap.firstElementChild.style.setProperty('overflow', 'auto', 'important');
      wrap.firstElementChild.style.setProperty('max-width', 'none', 'important');
      wrap.firstElementChild.style.setProperty('width', w + 'px', 'important');
      wrap.firstElementChild.style.setProperty('min-width', w + 'px', 'important');
    }}

    iframe.style.setProperty('width', w + 'px', 'important');
    iframe.style.setProperty('min-width', w + 'px', 'important');
    iframe.style.setProperty('height', h + 'px', 'important');
    iframe.style.setProperty('max-width', 'none', 'important');
    if (iframe.parentElement) {{
      iframe.parentElement.style.setProperty('width', w + 'px', 'important');
      iframe.parentElement.style.setProperty('min-width', w + 'px', 'important');
      iframe.parentElement.style.setProperty('max-width', 'none', 'important');
    }}
  }}
  setTimeout(forceScrollableCanvas, 60);
  setTimeout(forceScrollableCanvas, 260);
  setTimeout(forceScrollableCanvas, 700);
}})();
</script>
""",
        height=0,
    )

selection = st.session_state.current_selection
need_canvas_cleanup = False
if canvas_result and canvas_result.json_data:
    objects = canvas_result.json_data.get("objects", [])
    rects = [obj for obj in objects if obj.get("type") == "rect"]
    if rects:
        last_rect = rects[-1]
        new_selection = rect_to_selection(
            last_rect,
            img_w=img_w,
            img_h=img_h,
            canvas_w=canvas_width,
            canvas_h=canvas_height,
        )
        st.session_state.current_selection = new_selection
        selection = new_selection
    if len(rects) > 1:
        need_canvas_cleanup = True

with panel_col:
    action_taken = False
    st.markdown('<div class="right-panel-top"></div>', unsafe_allow_html=True)
    if selection:
        st.markdown(
            f'<span class="status-pill ok">{t("selection_ready")}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="status-pill info">{t("select_first")}</span>',
            unsafe_allow_html=True,
        )

    if st.button(
        t("remove_text"),
        type="primary",
        use_container_width=True,
        disabled=selection is None,
    ):
        with st.spinner(t("spinner_remove")):
            action_taken = True
            push_history(st.session_state.current_image)
            clean_image, text = logic.process_selected_area(
                st.session_state.current_image, selection
            )
            st.session_state.current_image = clean_image
            st.session_state.extracted_text = text if text else t("no_text")
            push_extracted_text(st.session_state.extracted_text)
            st.session_state.canvas_key += 1
            st.rerun()

    if st.button(
        t("extract_only"),
        use_container_width=True,
        disabled=selection is None,
    ):
        with st.spinner(t("spinner_extract")):
            action_taken = True
            text = logic.extract_text_only(st.session_state.current_image, selection)
            st.session_state.extracted_text = text if text else t("no_text")
            push_extracted_text(st.session_state.extracted_text)
            st.rerun()
    history = st.session_state.get("extracted_history", ["", "", ""])
    for idx in range(3):
        row_text_col, row_btn_col = st.columns([8.8, 1.2])
        with row_text_col:
            state_key = f"text_history_{idx}"
            if state_key not in st.session_state:
                st.session_state[state_key] = history[idx]
            st.text_area(
                f"text_history_label_{idx}",
                height=85,
                key=state_key,
                label_visibility="collapsed",
                placeholder=t("text_box_placeholder"),
            )
        with row_btn_col:
            current_text = st.session_state.get(state_key, "")
            b64_text = base64.b64encode(current_text.encode("utf-8")).decode()
            text_copy_fail = t("copy_text_fail")
            text_icon_html = f"""
<button id="clip-text-btn-{idx}" onclick="copyTextToClipboard{idx}()" style="
  width:100%;height:42px;margin-top:2px;
  background:#f0f2f6;border:1px solid #d0d4da;border-radius:8px;
  cursor:pointer;font-size:18px;color:#31333f;font-family:Segoe UI,sans-serif;">
  ⎘
</button>
<script>
function copyTextToClipboard{idx}() {{
  var btn = document.getElementById('clip-text-btn-{idx}');
  var text = new TextDecoder().decode(Uint8Array.from(atob('{b64_text}'), c => c.charCodeAt(0)));
  navigator.clipboard.writeText(text)
    .then(function() {{
      btn.textContent = '✓';
      btn.style.background = '#d4edda';
      setTimeout(function() {{
        btn.textContent = '⎘';
        btn.style.background = '#f0f2f6';
      }}, 1200);
    }})
    .catch(function() {{
      btn.textContent = '!';
      btn.title = '{text_copy_fail}';
      setTimeout(function() {{
        btn.textContent = '⎘';
      }}, 1500);
    }});
}}
</script>
"""
            st.components.v1.html(text_icon_html, height=44)

    if st.button(
        t("restore_bg"),
        use_container_width=True,
        disabled=selection is None,
    ):
        with st.spinner(t("spinner_restore")):
            try:
                action_taken = True
                clean_image = logic.inpaint_selection_only(st.session_state.current_image, selection)
                if clean_image is not None:
                    push_history(st.session_state.current_image)
                    st.session_state.current_image = clean_image
                    st.session_state.extracted_text = t("restore_done")
                    st.session_state.canvas_key += 1
                st.rerun()
            except Exception as e:
                st.error(str(e))

    image_bytes = current_image_bytes()
    st.download_button(
        t("download"),
        data=image_bytes,
        file_name=current_download_name(),
        mime="image/png",
        use_container_width=True,
    )

    btn_copy = t("copy_clipboard")
    copied = t("copied")
    copy_failed = t("copy_failed")
    b64_img = base64.b64encode(image_bytes).decode()
    clipboard_html = f"""
<button id="clip-btn" onclick="copyToClipboard()" style="
  width:100%;padding:8px 12px;margin-top:2px;
  background:#f0f2f6;border:1px solid #d0d4da;border-radius:8px;
  cursor:pointer;font-size:16px;color:#31333f;font-family:Segoe UI,sans-serif;">
  {btn_copy}
</button>
<script>
function copyToClipboard() {{
  var btn = document.getElementById('clip-btn');
  var byteChars = atob('{b64_img}');
  var arr = new Uint8Array(byteChars.length);
  for (var i = 0; i < byteChars.length; i++) arr[i] = byteChars.charCodeAt(i);
  var blob = new Blob([arr], {{type:'image/png'}});
  navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})])
    .then(function() {{
      btn.textContent = '{copied}';
      btn.style.background = '#d4edda';
      setTimeout(function() {{
        btn.textContent = '{btn_copy}';
        btn.style.background = '#f0f2f6';
      }}, 1800);
    }})
    .catch(function() {{
      btn.textContent = '{copy_failed}';
      setTimeout(function() {{
        btn.textContent = '{btn_copy}';
      }}, 2200);
    }});
}}
</script>
"""
    st.components.v1.html(clipboard_html, height=42)

if need_canvas_cleanup and not action_taken:
    st.session_state.canvas_key += 1
    st.rerun()
