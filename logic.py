import numpy as np
import easyocr
import torch
from simple_lama_inpainting import SimpleLama
from PIL import Image, ImageDraw, ImageFilter

# GPU 가속 사용 가능 여부 확인
USE_GPU = torch.cuda.is_available()

# AI 모델 로드
ocr_engine = easyocr.Reader(['ko', 'en'], gpu=USE_GPU)
lama_engine = SimpleLama()

def process_selected_area(original_image, selection_box):
    """
    선택된 영역에 대해:
    1. OCR로 텍스트 추출
    2. 텍스트 영역 마스킹
    3. Inpainting으로 배경 복원
    """
    # 좌표 정수 변환
    left = int(selection_box['left'])
    top = int(selection_box['top'])
    width = int(selection_box['width'])
    height = int(selection_box['height'])
    
    # 1. 이미지 크롭(선택 영역만 잘라냄)
    # 이미지 범위를 벗어나지 않도록 좌표 보정
    img_w, img_h = original_image.size
    left = max(0, left)
    top = max(0, top)
    right = min(img_w, left + width)
    bottom = min(img_h, top + height)
    
    # LaMa 품질 향상: 선택 영역 주변 context를 포함한 넓은 영역을 crop
    context_pad = 60
    ctx_left   = max(0, left - context_pad)
    ctx_top    = max(0, top - context_pad)
    ctx_right  = min(img_w, right + context_pad)
    ctx_bottom = min(img_h, bottom + context_pad)

    crop_img = original_image.crop((ctx_left, ctx_top, ctx_right, ctx_bottom))
    crop_img = crop_img.convert("RGB")

    # 선택 영역의 context crop 내 상대 좌표
    rel_left   = left   - ctx_left
    rel_top    = top    - ctx_top
    rel_right  = right  - ctx_left
    rel_bottom = bottom - ctx_top

    # 2. OCR 수행 (EasyOCR) — 원본 선택 영역만 crop해서 OCR
    ocr_crop_np = np.array(original_image.crop((left, top, right, bottom)).convert("RGB"))
    # EasyOCR readtext returns: (bbox, text, confidence)
    ocr_results = ocr_engine.readtext(ocr_crop_np)

    extracted_texts = []
    # 마스크 생성 (context crop 크기 기준, 검은 배경)
    mask = Image.new('L', crop_img.size, 0)
    draw = ImageDraw.Draw(mask)

    for (bbox, text, prob) in ocr_results:
        extracted_texts.append(text)
        # EasyOCR bbox: [[x,y], [x,y], [x,y], [x,y]]
        # OCR 좌표는 선택 영역 기준 → context crop 기준으로 오프셋 적용
        polygon = [(p[0] + rel_left, p[1] + rel_top) for p in bbox]
        draw.polygon(polygon, outline=255, fill=255)

    # 텍스트가 감지되지 않았다면 선택 영역 전체를 마스킹
    if not extracted_texts:
        draw.rectangle((rel_left, rel_top, rel_right, rel_bottom), fill=255)

    # 마스크 팽창(Dilation): 텍스트 잔상 제거를 위해 마스크를 살짝 확장
    mask = mask.filter(ImageFilter.MaxFilter(7))

    # 3. Inpainting (LaMa)
    try:
        clean_crop = lama_engine(crop_img, mask)
        result_region = clean_crop.crop((rel_left, rel_top, rel_right, rel_bottom))
    except Exception as e:
        print(f"Inpainting Error: {e}")
        result_region = original_image.crop((left, top, right, bottom))

    # 4. 원본 이미지에 합성
    final_image = original_image.copy()
    final_image.paste(result_region, (left, top))
    
    full_text = " ".join(extracted_texts)
    return final_image, full_text


def extract_text_only(original_image, selection_box):
    """
    선택된 영역에서 텍스트만 OCR로 추출
    """
    left   = int(selection_box['left'])
    top    = int(selection_box['top'])
    width  = int(selection_box['width'])
    height = int(selection_box['height'])

    img_w, img_h = original_image.size
    left   = max(0, left)
    top    = max(0, top)
    right  = min(img_w, left + width)
    bottom = min(img_h, top + height)

    ocr_crop_np = np.array(original_image.crop((left, top, right, bottom)).convert("RGB"))
    ocr_results = ocr_engine.readtext(ocr_crop_np)

    extracted_texts = [res[1] for res in ocr_results]
    return " ".join(extracted_texts)


def inpaint_selection_only(original_image, selection_box):
    """
    선택 영역 전체를 OCR 없이 마스크 처리해 인페인팅.
    """
    left = int(selection_box["left"])
    top = int(selection_box["top"])
    width = int(selection_box["width"])
    height = int(selection_box["height"])

    img_w, img_h = original_image.size
    left = max(0, left)
    top = max(0, top)
    right = min(img_w, left + width)
    bottom = min(img_h, top + height)
    if right - left <= 1 or bottom - top <= 1:
        return original_image.copy()

    context_pad = 60
    ctx_left = max(0, left - context_pad)
    ctx_top = max(0, top - context_pad)
    ctx_right = min(img_w, right + context_pad)
    ctx_bottom = min(img_h, bottom + context_pad)

    crop_img = original_image.crop((ctx_left, ctx_top, ctx_right, ctx_bottom)).convert("RGB")

    rel_left = left - ctx_left
    rel_top = top - ctx_top
    rel_right = right - ctx_left
    rel_bottom = bottom - ctx_top

    mask = Image.new("L", crop_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((rel_left, rel_top, rel_right, rel_bottom), fill=255)
    mask = mask.filter(ImageFilter.MaxFilter(7))

    try:
        clean_crop = lama_engine(crop_img, mask)
        result_region = clean_crop.crop((rel_left, rel_top, rel_right, rel_bottom))
    except Exception as e:
        raise RuntimeError(f"Inpainting Error: {e}") from e

    final_image = original_image.copy()
    final_image.paste(result_region, (left, top))
    return final_image
