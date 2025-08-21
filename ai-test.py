import google.generativeai as genai
from PIL import Image

# Gemini API 키 설정
API_KEY = "AIzaSyCZOj7nYhzQfu1BYGI_58cnxWKopxjzilI"
genai.configure(api_key=API_KEY)

# 모델 불러오기
model = genai.GenerativeModel("gemini-1.5-flash")

# 이미지 열기
organ = Image.open("images/2.png")

# 이미지와 질문 전달
response = model.generate_content(["첨부한 이미지에 대해 설명해줘", organ])



# 결과 출력
print(response.text)
