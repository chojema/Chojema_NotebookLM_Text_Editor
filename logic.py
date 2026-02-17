import numpy as np
from paddleocr import PaddleOCR
from simple_lama_inpainting import SimpleLama
from PIL import Image, ImageDraw

# AI 모델 로드(최초 실행 시 자동 다운로드)
# show_log=False로 불필요한 로그 숨김
ocr_engine = PaddleOCR(use_angle_cls=True, lang='korean', show_log=False)
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
    
    crop_img = original_image.crop((left, top, right, bottom))
    crop_np = np.array(crop_img)

    # 2. OCR 수행
    ocr_result = ocr_engine.ocr(crop_np, cls=True)
    
    extracted_texts = []
    # 마스크 생성(검은 배경)
    mask = Image.new('L', crop_img.size, 0)
    draw = ImageDraw.Draw(mask)

    if ocr_result and ocr_result[0]:
        for line in ocr_result[0]:
            text = line[1][0]
            box = line[0] # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
            extracted_texts.append(text)
            
            # 마스크 그리기(텍스트 영역을 흰색으로)
            polygon = [tuple(point) for point in box]
            draw.polygon(polygon, outline=255, fill=255)
            
            # 텍스트 주변을 살짝 더 넓게 칠하기(잔상 제거용 Dilation 효과)
            # 필요시 draw.line 등으로 두께 조절 가능

    # 3. Inpainting (LaMa)
    # 텍스트가 감지되지 않았다면 선택 영역 전체를 지움
    if not extracted_texts:
        draw.rectangle((0, 0, width, height), fill=255)
    
    # AI로 배경 복원
    try:
        clean_crop = lama_engine(crop_img, mask)
    except Exception as e:
        print(f"Inpainting Error: {e}")
        clean_crop = crop_img # 에러 시 원본 반환
    
    # 4. 원본 이미지에 합성
    final_image = original_image.copy()
    final_image.paste(clean_crop, (left, top))
    
    # 추출된 텍스트 합치기
    full_text = " ".join(extracted_texts)
    
    return final_image, full_text