import google.generativeai as genai
import os
from typing import Optional
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import logging

# HEIC 형식 지원
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    logger = logging.getLogger(__name__)
    logger.info("HEIC 형식 지원 활성화")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("pillow-heif이 설치되지 않아 HEIC 형식을 지원하지 않습니다.")

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# .env 파일 로드 (절대 경로 사용)
import os
from pathlib import Path

# 현재 파일의 디렉토리를 기준으로 .env 파일 경로 설정
current_dir = Path(__file__).parent.parent.parent
env_path = current_dir / ".env"
load_dotenv(env_path)

class AIService:
    def __init__(self):
        # .env 파일에서 API 키 가져오기
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        logger.info(f"API 키 로드 상태: {'성공' if GEMINI_API_KEY else '실패'}")
        
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        logger.info("Gemini API 초기화 중...")
        genai.configure(api_key=GEMINI_API_KEY)
        # 멀티모달(이미지+텍스트) 입력을 지원하는 1.5 Flash 사용
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API 초기화 완료")
    
    def _optimize_image(self, image: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        이미지를 AI 분석에 최적화합니다.
        """
        width, height = image.size
        
        # 너무 큰 이미지만 리사이즈 (성능 최적화)
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"이미지 리사이즈: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    async def analyze_image_from_path(self, image_path: str) -> Optional[str]:
        """
        이미지 파일 경로를 받아서 분석합니다. (ai-test.py와 동일한 방식)
        """
        try:
            logger.info(f"이미지 파일 분석 시작: {image_path}")
            
            # 파일 존재 확인
            if not os.path.exists(image_path):
                logger.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None
            
            # 파일 크기 확인
            file_size = os.path.getsize(image_path)
            logger.info(f"파일 크기: {file_size} bytes")
            
            if file_size == 0:
                logger.error("빈 파일입니다.")
                return None
            
            # ai-test.py와 동일한 방식: PIL Image 객체 생성
            try:
                image = Image.open(image_path)
                logger.info(f"PIL Image 로드 성공: {image.format}, 크기: {image.size}, 모드: {image.mode}")
            except Exception as img_error:
                logger.error(f"PIL Image 로드 실패: {img_error}")
                return f"이미지 형식을 인식할 수 없습니다: {str(img_error)}"
            
            # 이미지가 제대로 로드되었는지 확인
            if not image:
                logger.error("이미지 객체가 None입니다.")
                return "이미지를 로드할 수 없습니다."
            
            # RGB 모드로 변환 (HEIC, RGBA 등 모든 형식을 RGB로)
            try:
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                    logger.info(f"이미지 모드 변환 완료: RGB")
            except Exception as convert_error:
                logger.error(f"이미지 모드 변환 실패: {convert_error}")
                return f"이미지 변환 중 오류가 발생했습니다: {str(convert_error)}"
            
            # 이미지 최적화
            try:
                image = self._optimize_image(image)
                logger.info(f"이미지 최적화 완료: {image.size}")
            except Exception as optimize_error:
                logger.error(f"이미지 최적화 실패: {optimize_error}")
                # 최적화 실패해도 원본 이미지로 계속 진행
            
            # AI 분석을 위한 상세한 프롬프트
            prompt = """
            이 이미지를 분석하여 다음 정보를 포함한 자연스러운 설명을 생성해주세요:
            
            1. 장소 유형 (예: 놀이터, 카페, 공원, 골목, 건물 등 구체적인 장소)
            2. 주요 요소 (예: 회전무대, 벤치, 나무, 벽화 등)
            3. 분위기 (예: 한적한, 활발한, 고즈넉한, 아름다운 등)
            
            설명은 한국어로 작성하고, 자연스러운 한 문장으로 구성해주세요.
            예시: "한적한 분위기의 놀이터로, 회전무대와 그네가 있는 아담한 공간입니다."
            """
            
            logger.info("AI 분석 요청 시작 (PIL Image 객체 전달)")
            
            # ai-test.py와 동일한 방식: PIL Image 객체를 Gemini API에 직접 전달
            response = self.model.generate_content([prompt, image])
            
            if response.text:
                logger.info("AI 분석 완료")
                return response.text.strip()
            else:
                logger.warning("AI 분석 결과가 비어있습니다")
                return "이미지 분석을 완료할 수 없습니다."
                
        except Exception as e:
            logger.error(f"AI 분석 중 오류 발생: {e}")
            logger.error(f"오류 타입: {type(e)}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"

# 전역 AI 서비스 인스턴스
ai_service = AIService()
