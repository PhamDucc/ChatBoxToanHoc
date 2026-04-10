import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
from PIL import Image

# CHÌA KHÓA VÀNG CỦA ĐỨC
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# HÀM RADAR: Tự động lên máy chủ quét xem con AI miễn phí nào đang sống
@st.cache_data(ttl=600) # Quét 10 phút một lần cho đỡ nặng
def get_live_free_models():
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
        if response.status_code == 200:
            data = response.json().get('data', [])
            # Gom tất cả các con AI có chữ "free" ở cuối tên
            return [m['id'] for m in data if m['id'].endswith(':free')]
    except Exception as e:
        print(f"Lỗi quét Radar: {e}")
    # Nếu radar hỏng, dùng danh sách dự phòng bất tử này
    return [
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "qwen/qwen-2-7b-instruct:free"
    ]

def solve_math_openrouter(query, img=None):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    user_content = []
    if query:
        user_content.append({"type": "text", "text": query})
    if img:
        if img.mode != 'RGB': img = img.convert('RGB')
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

    # Lấy danh sách hàng chục con AI miễn phí đang mở cửa ngay lúc này
    models_to_try = get_live_free_models()
    
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Bạn là giáo viên dạy Toán. Hãy giải chi tiết từng bước, sử dụng LaTeX. Trả lời hoàn toàn bằng tiếng Việt."},
                    {"role": "user", "content": user_content}
                ],
            )
            # Thành công phát là trả về luôn, kèm theo tên con AI đang vác tù và hàng tổng
            return "Tớ xong rùi nè, hehe\n\n" + response.choices[0].message.content
        except Exception as e:
            # Nếu con này lỗi (ví dụ không biết đọc ảnh hoặc bị 404), câm nín bỏ qua và thử con khác
            print(f"Con AI {model_name} ngỏm củ tỏi: {e}")
            continue 
            
    return "Huhu, nay tớ học động hết công suất rùi, bạn cho tớ nghỉ tới ngày mai nha."

# --- GIAO DIỆN TRỢ LÝ CỦA MẸ LAN ---
st.set_page_config(page_title="Chatbox AI cô Lan", layout="centered")
st.header("🎓 Trợ lý Toán học của cô Lan xinh")

query = st.text_area("Nhập đề bài tại đây:", placeholder="Ví dụ: giải phương trình x^2 - 5x + 6 = 0")
uploaded_file = st.file_uploader("Hoặc chụp ảnh gửi bài cho tớ:", type=['jpg', 'png', 'jpeg'])

if st.button("Bạn click vào đây để mình giải nhé"):
    if query or uploaded_file:
        img_to_send = None
        if uploaded_file:
            img_to_send = Image.open(uploaded_file)
            st.image(img_to_send, caption="Ảnh bạn gửi", width=300)
            
        with st.spinner("Đợi mình xíu, mình giải ra liền"):
            try:
                result = solve_math_openrouter(query, img_to_send)
                
                # BỘ LỌC CHUẨN CỦA DÂN PRO: Phân biệt được ngoặc toán học và lệnh xuống dòng
                result = re.sub(r'(?<!\\)\\\[', '$$', result)
                result = re.sub(r'(?<!\\)\\\]', '$$', result)
                result = result.replace(r'\(', '$').replace(r'\)', '$')
                
                st.markdown("### 📝 Lời giải chi tiết của bạn đây ạ:")
                st.markdown(result)
            except Exception as e:
                st.error(f"Tớ bị quá tải rùi huhu: {e}")
    else:
        st.warning("Bạn chưa nhập đề hoặc gửi ảnh kìa!")