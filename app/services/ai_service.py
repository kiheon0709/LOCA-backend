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
    
    def _optimize_image(self, image: Image.Image, max_size: int = 512) -> Image.Image:
        """
        이미지를 AI 분석에 최적화합니다.
        Gemini API는 이미지 크기에 제한이 있으므로 리사이즈합니다.
        """
        # 이미지 크기 확인
        width, height = image.size
        
        # 최대 크기보다 큰 경우 리사이즈
        if width > max_size or height > max_size:
            # 비율 유지하면서 리사이즈
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"이미지 리사이즈: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    async def analyze_image(self, image_data: bytes) -> Optional[str]:
        """
        이미지를 분석하여 장소 유형, 주요 요소, 분위기를 포함한 설명을 생성합니다.
        """
        try:
            # 이미지 데이터를 PIL Image로 변환 (HEIC 포함 모든 형식 지원)
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"이미지 로드 성공: {image.format}, 크기: {image.size}, 모드: {image.mode}")
            
            # RGB 모드로 변환 (HEIC, RGBA 등 모든 형식을 RGB로)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info(f"이미지 모드 변환 완료: RGB")
            
            # 이미지 최적화
            image = self._optimize_image(image)
            
            # AI 분석을 위한 상세한 프롬프트
            prompt = """
            이 이미지를 분석하여 다음 정보를 포함한 자연스러운 설명을 생성해주세요:
            
            1. 장소 유형 (예: 놀이터, 카페, 공원, 골목, 건물 등)
            2. 주요 요소 (예: 회전무대, 벤치, 나무, 벽화 등)
            3. 분위기 (예: 한적한, 활발한, 고즈넉한, 아름다운 등)
            
            설명은 한국어로 작성하고, 자연스러운 한 문장으로 구성해주세요.
            예시: "한적한 분위기의 놀이터로, 회전무대와 그네가 있는 아담한 공간입니다."
            """
            
            # AI 분석 실행 (타임아웃 설정 포함)
            import asyncio
            try:
                # 45초 타임아웃으로 AI 분석 실행
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.model.generate_content, [prompt, image]),
                    timeout=45.0
                )
                
                if response.text:
                    logger.info("AI 분석 완료")
                    return response.text.strip()
                else:
                    logger.warning("AI 분석 결과가 비어있습니다")
                    return "이미지 분석을 완료할 수 없습니다."
                    
            except asyncio.TimeoutError:
                logger.error("AI 분석 타임아웃 (45초 초과)")
                return "AI 분석 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
                
        except Exception as e:
            logger.error(f"AI 분석 중 오류 발생: {e}")
            # 네트워크 관련 오류인지 확인
            if "DNS" in str(e) or "timeout" in str(e).lower() or "503" in str(e):
                return "네트워크 연결 문제로 AI 분석을 할 수 없습니다. 인터넷 연결을 확인해주세요."
            else:
                return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"
    
    async def analyze_image_from_path(self, image_path: str) -> Optional[str]:
        """
        이미지 파일 경로를 받아서 분석합니다.
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return await self.analyze_image(image_data)
        except FileNotFoundError:
            logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            return None
        except Exception as e:
            logger.error(f"이미지 파일 읽기 중 오류 발생: {e}")
            return None

# 전역 AI 서비스 인스턴스
ai_service = AIService()
