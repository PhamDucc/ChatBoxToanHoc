import streamlit as st
from openai import OpenAI
import base64
import io
import requests
import re
import random  # Đã thêm thư viện random để xáo trộn chìa khóa
from PIL import Image

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
    user_content = []
    if query:
        user_content.append({"type": "text", "text": query})
    if img:
        if img.mode != 'RGB': img = img.convert('RGB')
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

    # Lấy danh sách hàng chục con AI miễn phí đang mở cửa
    models_to_try = get_live_free_models()
    
    # 1. LẤY DANH SÁCH 5 CHÌA KHÓA VÀ XÁO TRỘN NGẪU NHIÊN
    danh_sach_keys = list(st.secrets["OPENROUTER_API_KEY"])
    random.shuffle(danh_sach_keys)
    
    # 2. VÒNG LẶP DỰ PHÒNG: Thử từng chìa khóa một
    for api_key in danh_sach_keys:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        for model_name in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        # Lời nguyền ép AI dùng định dạng Toán học chuẩn
                        {"role": "system", "content": "..."},
                        {"role": "user", "content": user_content}
                    ],
                )
                # Thành công phát là trả về luôn, kèm theo câu chào
                return "Tớ xong rùi nè, hehe\n\n" + response.choices[0].message.content
            except Exception as e:
                # Nếu lỗi (hết lượt hoặc nghẽn mạng), in ra log và câm nín thử tiếp
                print(f"Lỗi với Key đuôi ...{api_key[-4:]} - Model {model_name}: {e}")
                continue 
            
    # Nếu chạy qua cả 5 chìa khóa, quét qua cả chục con AI mà vẫn lỗi thì mới in ra câu này
    return "Huhu, nay tớ hoạt động hết công suất rùi, bạn cho tớ nghỉ tới sáng mai nha "
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
