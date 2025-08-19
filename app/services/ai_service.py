import google.generativeai as genai
import os
from typing import Optional
import base64
from PIL import Image
import io

class AIService:
    def __init__(self):
        # 환경변수에서 API 키 가져오기 (실제 배포 시에는 환경변수 사용)
        api_key = os.getenv("GEMINI_API_KEY", "your-api-key-here")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
    
    async def analyze_image(self, image_data: bytes) -> Optional[str]:
        """
        이미지를 분석하여 장소 유형, 주요 요소, 분위기를 포함한 설명을 생성합니다.
        """
        try:
            # 이미지 데이터를 PIL Image로 변환
            image = Image.open(io.BytesIO(image_data))
            
            # AI 분석을 위한 프롬프트
            prompt = """
            이 이미지를 분석하여 다음 정보를 포함한 자연스러운 설명을 생성해주세요:
            
            1. 장소 유형 (예: 놀이터, 카페, 공원, 골목, 건물 등)
            2. 주요 요소 (예: 회전무대, 벤치, 나무, 벽화 등)
            3. 분위기 (예: 한적한, 활발한, 고즈넉한, 아름다운 등)
            
            설명은 한국어로 작성하고, 자연스러운 문장으로 구성해주세요.
            예시: "한적한 분위기의 놀이터로, 회전무대와 그네가 있는 아담한 공간입니다."
            """
            
            # AI 분석 실행
            response = self.model.generate_content([prompt, image])
            
            if response.text:
                return response.text.strip()
            else:
                return "이미지 분석을 완료할 수 없습니다."
                
        except Exception as e:
            print(f"AI 분석 중 오류 발생: {e}")
            return "이미지 분석 중 오류가 발생했습니다."
    
    async def analyze_image_from_path(self, image_path: str) -> Optional[str]:
        """
        이미지 파일 경로를 받아서 분석합니다.
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return await self.analyze_image(image_data)
        except Exception as e:
            print(f"이미지 파일 읽기 중 오류 발생: {e}")
            return None

# 전역 AI 서비스 인스턴스
ai_service = AIService()
