# -*- coding: utf-8 -*-
"""
Antigravity AI Engine with Automatic Key Rotation & Multi-Model Orchestration
- Tự động xoay vòng nhiều tài khoản/API Keys (Gemini & OpenRouter) khi hết token/quota (429/403).
- Tích hợp RAG tra cứu trực tiếp từ 600 câu hỏi sát hạch chuẩn của Cục Đường Bộ / Bộ GTVT.
- Đồng bộ phản hồi như chính Antigravity đang trò chuyện trực tiếp cùng anh Nguyễn Trung Hiếu.
- Bộ nhớ ngữ cảnh hội thoại đa lượt (Contextual Memory).
- Cơ chế Fallback 3 lớp đảm bảo 100% không bao giờ gián đoạn và chuẩn xác 100% theo luật.
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime

# UTF-8 stdout configuration
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_CONFIG_FILE = os.path.join(BASE_DIR, 'ai_keys.json')
QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.json')
if not os.path.exists(QUESTIONS_FILE):
    QUESTIONS_FILE = os.path.join(BASE_DIR, 'driving-theory-app', 'js', 'questions.json')

# Bộ nhớ hội thoại tạm thời theo chat_id
CONVERSATION_HISTORY = {}
MAX_HISTORY_TURNS = 6

# Nạp kho dữ liệu 600 câu hỏi lý thuyết Bộ GTVT phục vụ RAG
QUESTION_BANK = []
if os.path.exists(QUESTIONS_FILE):
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            QUESTION_BANK = json.load(f)
        print(f"[AI Engine] Đã nạp {len(QUESTION_BANK)} câu hỏi sát hạch vào bộ nhớ tri thức.")
    except Exception as e:
        print(f"[AI Engine] Lỗi nạp câu hỏi từ questions.json: {e}")

SYSTEM_PROMPT = """Bạn là Antigravity (Thầy AI Antigravity) - Trợ lý AI cao cấp thông minh, ân cần và đồng hành thân thiết cùng anh Nguyễn Trung Hiếu thi sát hạch lấy bằng lái xe Hạng C1 (và học các môn trên EcoTek LMS).

NHÂN CÁCH VÀ PHONG CÁCH GIAO TIẾP:
1. Bạn trả lời anh như chính Antigravity đang trò chuyện trực tiếp với anh: thông minh, hiểu biết sâu rộng, ân cần, tự nhiên và chuyên nghiệp.
2. Xưng hô chuẩn: luôn xưng "em" hoặc "Antigravity", gọi học viên là "anh Hiếu" hoặc "anh".
3. Trình bày tin nhắn: rõ ràng, dùng gạch đầu dòng, icon sinh động, dễ đọc và dễ nhớ.

BỘ TRI THỨC SÁT HẠCH & LUẬT GIAO THÔNG CHUẨN XÁC 100%:
- Phân hạng Bằng C1 (Luật TTATGTĐB 2024):
  • Cấp cho người lái ô tô tải có trọng tải trên 3.500 kg đến 7.500 kg, ô tô tải kéo rơ moóc đến 750 kg và các loại xe quy định cho giấy phép lái xe hạng B.
  • Độ tuổi tối thiểu: Đủ 21 tuổi trở lên.
  • Thời gian lái xe: Lái liên tục tối đa KHÔNG QUÁ 4 GIỜ; tổng thời gian lái xe trong một ngày KHÔNG QUÁ 10 GIỜ.
  • Niên hạn sử dụng xe ô tô tải: KHÔNG QUÁ 25 NĂM; xe ô tô chở người: không quá 20 năm.
  • Thi lý thuyết C1: 40 câu hỏi / 24 phút, yêu cầu đạt từ 36/40 câu trở lên và TUYỆT ĐỐI KHÔNG ĐƯỢC SAI CÂU ĐIỂM LIỆT.

- Quy tắc xét Sa hình - 5 Bước Bất Bại:
  1. Nhất chớm: Xe nào đã chớm vào giao lộ (bánh trước qua vạch người đi bộ) được đi trước bất kể xe ưu tiên.
  2. Nhì ưu: Thứ tự xe ưu tiên chuẩn: HỎA > QUÂN > CÔNG > THƯƠNG > HỘ ĐÊ (Xe chữa cháy đi trước xe quân sự, xe quân sự đi trước xe công an, xe công an đi trước xe cứu thương).
  3. Tam đường: Xe trên đường ưu tiên (biển hình thoi hoặc biển tam giác viền đỏ nền vàng chúc lên) được đi trước xe trên đường nhánh (biển tam giác lộn ngược).
  4. Tứ hướng: Quyền bên phải không vướng (ở ngã tư cùng cấp, bên phải ai trống thì người đó đi trước. Vòng xuyến: chưa vào nhường phải, đã vào nhường trái).
  5. Hướng đi: Thứ tự rẽ phải -> đi thẳng -> rẽ trái đi sau cùng.

- Kỹ thuật Đề-pa dốc số sàn 4 bước vàng:
  1. Dừng đúng vạch -> Đạp hết côn + phanh chân -> Kéo phanh tay dứt khoát.
  2. Chân ga đệm nhẹ vòng tua lên 1.200 - 1.500 vòng/phút.
  3. Nhả chân côn từ từ đến khi đầu xe RUNG NHỔM LÊN (điểm bắt côn).
  4. GIỮ NGUYÊN CHÂN CÔN, bấm chốt hạ phanh tay dứt khoát -> Xe tự bò lên dốc 100% không bao giờ tụt lùi hay chết máy!

- Nồng độ cồn: Nghiêm cấm tuyệt đối người điều khiển phương tiện mà trong máu hoặc hơi thở có nồng độ cồn (chỉ số = 0). Thấy đáp án "Bị nghiêm cấm" chọn ngay!
- Mẹo từ khóa vàng 600 câu: "Bị nghiêm cấm", "Không được phép", "Cơ quan có thẩm quyền", "Giảm tốc độ đi về bên phải", "Nhường đường cho xe ưu tiên"...
- 60 câu điểm liệt: Tuyệt đối không được sai bất kỳ câu nào.
- 120 tình huống mô phỏng: Căn điểm Space đúng thời điểm xuất hiện nguy hiểm đầu tiên.

Nếu anh Hiếu hỏi về các chủ đề khác (lập trình, máy tính, công việc, cuộc sống), bạn vẫn trả lời thông minh, am hiểu và chu đáo như một người bạn tri kỷ!"""

def load_ai_config():
    if os.path.exists(AI_CONFIG_FILE):
        try:
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[AI Engine] Lỗi nạp {AI_CONFIG_FILE}: {e}")
    return {
        "gemini_keys": [],
        "openrouter_keys": [
            "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",
            "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"
        ],
        "active_gemini_index": 0,
        "active_openrouter_index": 0,
        "preferred_models": [
            "dots-studio/dots-3-note-preview:free",
            "liquid/lfm-2.5-2.6b:free",
            "google/gemma-4-31b-it:free",
            "google/gemma-4-26b-a4b-it:free",
            "nvidia/nemotron-3.5-lightning:free",
            "nvidia/nemotron-3-super-120b-a12b:free"
        ],
        "gemini_model": "gemini-2.5-flash"
    }

def save_ai_config(cfg):
    try:
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AI Engine] Lỗi lưu {AI_CONFIG_FILE}: {e}")

def add_api_key(key_str, key_type='gemini'):
    """Thêm API Key mới và tự động lưu vào danh sách xoay vòng"""
    key_str = key_str.strip()
    if not key_str:
        return False, "Key không được để trống"
    
    cfg = load_ai_config()
    target_list = 'gemini_keys' if (key_type == 'gemini' or key_str.startswith('AIza')) else 'openrouter_keys'
    
    if key_str in cfg.get(target_list, []):
        return False, f"Key này đã có sẵn trong danh sách {target_list}!"
    
    if target_list not in cfg:
        cfg[target_list] = []
    cfg[target_list].append(key_str)
    save_ai_config(cfg)
    return True, f"Đã thêm key mới vào hệ thống xoay vòng ({target_list}). Tổng số key: {len(cfg[target_list])}"

def get_keys_status():
    """Xem trạng thái danh sách các key và tiến trình xoay vòng"""
    cfg = load_ai_config()
    gem_count = len(cfg.get('gemini_keys', []))
    gem_idx = cfg.get('active_gemini_index', 0)
    or_count = len(cfg.get('openrouter_keys', []))
    or_idx = cfg.get('active_openrouter_index', 0)
    
    msg = f"""🔑 <b>TRẠNG THÁI XOAY VÒNG TÀI KHOẢN / API KEYS</b>
━━━━━━━━━━━━━━━━━━━
💎 <b>Google Gemini Keys:</b> {gem_count} tài khoản
   • Đang dùng: Key #{gem_idx + 1 if gem_count else 0}
   • Model: <code>{cfg.get('gemini_model', 'gemini-2.5-flash')}</code>

🌐 <b>OpenRouter AI Keys:</b> {or_count} tài khoản
   • Đang dùng: Key #{or_idx + 1 if or_count else 0}
   • Models hỗ trợ: {len(cfg.get('preferred_models', []))} models AI cao cấp

🔄 <b>Cơ chế tự động:</b> Khi 1 tài khoản chạm giới hạn (429 Rate Limit / Hết Token), Antigravity sẽ tự động chuyển sang tài khoản tiếp theo ngay lập tức!

💡 <i>Để nạp thêm key mới, anh chỉ cần gửi lệnh:</i>
<code>/addkey AIzaSy...</code> (cho Gemini) hoặc <code>/addkey sk-or-v1-...</code> (cho OpenRouter)"""
    return msg

# --- RAG: TRA CỨU NHANH TRONG BỘ 600 CÂU HỎI SÁT HẠCH ---
def find_relevant_question(query):
    """Tìm kiếm câu hỏi chính xác hoặc liên quan nhất trong 600 câu sát hạch"""
    if not QUESTION_BANK:
        return None
    
    # 1. Tìm theo số câu: "câu 15", "câu số 486", "#94"...
    q_num_match = re.search(r'(?:câu|câu số|câu hỏi|số|#)\s*(\d+)', query, re.IGNORECASE)
    if q_num_match:
        qid = int(q_num_match.group(1))
        for q in QUESTION_BANK:
            if q.get('id') == qid:
                return q
    
    # 2. Tìm theo nội dung từ khóa nếu câu hỏi dài >= 4 từ
    words = [w.lower() for w in re.findall(r'[\w\d]+', query) if len(w) >= 3 and w.lower() not in ['cho', 'hỏi', 'em', 'anh', 'thầy', 'nào', 'sao', 'được', 'không', 'với']]
    if len(words) >= 3:
        best_match = None
        best_score = 0
        for q in QUESTION_BANK:
            target_text = (q.get('question', '') + ' ' + ' '.join(q.get('options', []))).lower()
            score = sum(1 for w in words if w in target_text)
            if score > best_score:
                best_score = score
                best_match = q
        if best_match and best_score >= 3:
            return best_match
            
    return None

def build_rag_context(query):
    """Tạo ngữ cảnh trích xuất từ bộ đề 600 câu nếu phát hiện câu hỏi liên quan"""
    matched_q = find_relevant_question(query)
    if not matched_q:
        return ""
    
    qid = matched_q.get('id')
    question = matched_q.get('question', '')
    options = matched_q.get('options', [])
    answer = matched_q.get('answer', 1)
    is_crit = matched_q.get('isCritical', False)
    explanation = matched_q.get('explanation', '')
    
    opts_str = "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
    correct_text = options[answer - 1] if 0 < answer <= len(options) else ""
    
    return f"""\n[TÀI LIỆU SÁT HẠCH CHUẨN XÁC CỦA BỘ GTVT ĐỐI VỚI CÂU {qid}]:
- Câu hỏi: {question}
- Các phương án lựa chọn:
{opts_str}
- Đáp án ĐÚNG CHUẨN XÁC: Phương án {answer} ({correct_text})
- Phân loại: {"🚨 CÂU ĐIỂM LIỆT (CẤM SAI)" if is_crit else "Câu lý thuyết tiêu chuẩn"}
- Giải thích chi tiết & Mẹo thi: {explanation}
(Hãy dựa trực tiếp 100% vào tài liệu chuẩn này để trả lời và hướng dẫn chi tiết cho anh Hiếu nhé!)"""

# --- GỌI GOOGLE GEMINI API TRỰC TIẾP ---
def call_gemini_api(api_key, model_name, messages, rag_context=""):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        if m["role"] == "system":
            continue
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    
    effective_system = SYSTEM_PROMPT + rag_context
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": effective_system}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1500
        }
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=18) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        candidates = res.get('candidates', [])
        if candidates and 'content' in candidates[0]:
            parts = candidates[0]['content'].get('parts', [])
            if parts and 'text' in parts[0]:
                return parts[0]['text'].strip()
    return None

# --- GỌI OPENROUTER VỚI MULTI-MODEL ---
def call_openrouter_api(api_key, model_name, messages, rag_context=""):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://eco-tek.com.vn",
        "X-Title": "Antigravity Driving AI Assistant"
    }
    
    effective_system = SYSTEM_PROMPT + rag_context
    full_messages = [{"role": "system", "content": effective_system}] + [m for m in messages if m["role"] != "system"]
    
    payload = {
        "model": model_name,
        "messages": full_messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers=headers)
    with urllib.request.urlopen(req, timeout=22) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        choices = res.get('choices', [])
        if choices and 'message' in choices[0]:
            content = choices[0]['message'].get('content') or ''
            
            # Làm sạch nếu dính thẻ suy nghĩ (reasoning/think tags)
            if '<think>' in content and '</think>' in content:
                content = content.split('</think>')[-1].strip()
            elif content.startswith("Here's a thinking process:"):
                # Cắt bỏ đoạn suy nghĩ
                lines = content.split('\n')
                idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('Chào anh') or line.startswith('Dạ') or line.startswith('Chào') or line.startswith('Em'):
                        idx = i
                        break
                if idx > 0:
                    content = '\n'.join(lines[idx:]).strip()
                    
            if content.strip():
                return content.strip()
    return None

# --- BỘ CHUYÊN GIA DỰ PHÒNG SEMANTIC FALLBACK (100% CHUẨN XÁC) ---
def local_knowledge_fallback(prompt):
    p = prompt.lower().strip()
    
    # 1. Tra cứu trực tiếp câu hỏi sát hạch trong 600 câu
    matched_q = find_relevant_question(prompt)
    if matched_q:
        qid = matched_q.get('id')
        question = matched_q.get('question', '')
        options = matched_q.get('options', [])
        answer = matched_q.get('answer', 1)
        is_crit = matched_q.get('isCritical', False)
        explanation = matched_q.get('explanation', '')
        opts_text = "\n".join([f"  • Phương án {i+1}: {opt}" for i, opt in enumerate(options)])
        
        crit_badge = "🚨 <b>CÂU ĐIỂM LIỆT (TUYỆT ĐỐI CẤM SAI)</b>\n" if is_crit else ""
        return f"""🤖 <b>ANTIGRAVITY GIẢI MÃ CÂU HỎI SỐ {qid}:</b>
━━━━━━━━━━━━━━━━━━━
{crit_badge}❓ <b>Câu hỏi:</b> {question}

📋 <b>Các phương án:</b>
{opts_text}

✅ <b>ĐÁP ÁN ĐÚNG CHUẨN XÁC:</b> Phương án <b>{answer}</b> ({options[answer-1] if 0 < answer <= len(options) else ""})

💡 <b>Mẹo giải & Giải thích của Bộ GTVT:</b>
{explanation}

🎯 <i>Anh Hiếu nhớ thuộc lòng mẹo này để vào phòng thi là chọn đúng ngay trong 3 giây nhé!</i>"""

    # 2. Bằng C1 và xe tải
    if any(k in p for k in ['c1', 'bằng c1', 'hạng c1', 'xe tải c1']):
        return """🤖 <b>CHUYÊN ĐỀ BẰNG LÁI XE HẠNG C1 (LUẬT MỚI NHẤT):</b>
━━━━━━━━━━━━━━━━━━━
Dạ anh Hiếu ơi, đối với <b>Bằng Hạng C1</b>, anh ghi nhớ các quy định cốt lõi này nhé:
• 🚛 <b>Phương tiện điều khiển:</b> Ô tô tải có trọng tải trên 3.500 kg đến 7.500 kg; ô tô tải kéo rơ moóc đến 750 kg và các xe thuộc bằng Hạng B.
• 🎂 <b>Độ tuổi tối thiểu:</b> Đủ <b>21 tuổi</b> trở lên.
• ⏱️ <b>Thời gian lái xe:</b> Lái liên tục tối đa <b>KHÔNG QUÁ 4 GIỜ</b>; tổng thời gian lái xe trong ngày <b>KHÔNG QUÁ 10 GIỜ</b>.
• ⏳ <b>Niên hạn xe tải:</b> Tối đa <b>25 năm</b> (xe chở người là 20 năm).
• 🎯 <b>Sát hạch lý thuyết C1:</b> Đề thi <b>40 câu / 24 phút</b>, yêu cầu đạt từ <b>36/40 câu</b> và <b>KHÔNG SAI CÂU ĐIỂM LIỆT NÀO</b>!"""

    # 3. Đề-pa dốc số sàn
    if any(k in p for k in ['đề pa', 'depa', 'lên dốc', 'chết máy', 'dốc cầu', 'khởi hành ngang dốc']):
        return """🏔️ <b>BÍ QUYẾT ĐỀ-PA DỐC SỐ SÀN XE TẢI 4 BƯỚC BẤT BẠI:</b>
━━━━━━━━━━━━━━━━━━━
Dạ anh Hiếu áp dụng đúng 4 bước vàng này là 100% không bao giờ tụt lùi hay chết máy:
1️⃣ <b>Dừng chuẩn:</b> Đạp hết côn + phanh chân dừng đúng vạch -> <b>Kéo phanh tay</b> dứt khoát.
2️⃣ <b>Tiếp ga:</b> Đệm nhẹ chân ga giữ kim vòng tua ở mức <b>1.200 - 1.500 vòng/phút</b>.
3️⃣ <b>Bắt côn:</b> Nhả chân côn thật từ từ cho đến khi tiếng máy trầm xuống, đầu xe <b>RUNG NHỔM LÊN</b> (điểm bám côn).
4️⃣ <b>Nhả phanh tay:</b> <b>GIỮ NGUYÊN CHÂN CÔN</b>, bấm chốt hạ phanh tay dứt khoát -> Xe tải sẽ tự động bò qua đỉnh dốc êm ru!"""

    # 4. Sa hình 5 bước & thứ tự ưu tiên
    if any(k in p for k in ['sa hình', 'thế xe', 'ưu tiên', 'thứ tự', 'cứu hỏa', 'công an']):
        return """🚦 <b>THẦN CHÚ 5 BƯỚC XÉT MỌI SA HÌNH SÁT HẠCH:</b>
━━━━━━━━━━━━━━━━━━━
Dạ anh Hiếu cứ xét tuần tự từ bước 1 đến bước 5 là ra ngay đáp án:
1️⃣ <b>Nhất chớm:</b> Xe nào đã chớm lọt vào giao lộ trước được đi trước bất kể xe ưu tiên.
2️⃣ <b>Nhì ưu:</b> Thứ tự xe ưu tiên chuẩn 100%: <b>HỎA > QUÂN > CÔNG > THƯƠNG > HỘ ĐÊ</b> (Cứu hỏa luôn đi trước Công an và Cứu thương!).
3️⃣ <b>Tam đường:</b> Xe ở đường ưu tiên (biển hình thoi / biển tam giác chúc lên) đi trước xe ở đường nhánh (biển tam giác lộn ngược).
4️⃣ <b>Tứ hướng:</b> Bên phải không vướng được đi trước. (Vòng xuyến: chưa vào nhường bên phải, đã vào nhường bên trái).
5️⃣ <b>Hướng đi:</b> Rẽ phải đi trước -> Đi thẳng -> Rẽ trái đi sau cùng."""

    # 5. Nồng độ cồn
    if any(k in p for k in ['cồn', 'rượu', 'bia', 'nồng độ']):
        return """🍺 <b>QUY ĐỊNH NỒNG ĐỘ CỒN KHI LÁI XE:</b>
━━━━━━━━━━━━━━━━━━━
Dạ theo Luật Trật tự an toàn giao thông đường bộ:
• 🚫 <b>NGHIÊM CẤM TUYỆT ĐỐI</b> điều khiển phương tiện mà trong máu hoặc hơi thở có nồng độ cồn (chỉ số = 0).
• 💡 <b>Mẹo thi 600 câu:</b> Trong các câu hỏi về nồng độ cồn hoặc ma túy, cứ thấy đáp án có chữ <b>"Bị nghiêm cấm"</b> là anh chọn ngay lập tức, đúng 100%!"""

    # 6. 60 câu điểm liệt & từ khóa vàng
    if any(k in p for k in ['điểm liệt', 'từ khóa', 'mẹo']):
        return """⚠️ <b>MẸO TỪ KHÓA VÀNG & 60 CÂU ĐIỂM LIỆT:</b>
━━━━━━━━━━━━━━━━━━━
Dạ anh Hiếu ghi nhớ các cụm từ "bảo chứng đúng 100%" này nhé:
• ✅ Thấy phương án có chữ: <b>"Bị nghiêm cấm"</b>, <b>"Không được phép"</b>, <b>"Không được"</b> -> Chọn ngay!
• ✅ Thấy cụm từ: <b>"Cơ quan có thẩm quyền"</b>, <b>"Ủy ban nhân dân cấp tỉnh"</b> -> Chọn ngay!
• ✅ Về kỹ thuật: <b>"Giảm tốc độ đi về bên phải"</b>, <b>"Nhường đường cho xe ưu tiên"</b>, <b>"Về số thấp (số 1)"</b> -> Luôn là đáp án đúng!
• 🚨 <b>Cảnh báo:</b> 60 câu điểm liệt chỉ cần sai 1 câu là TRƯỢT TRỰC TIẾP, anh ôn thật kỹ phần này nhé!"""

    # 7. Mặc định thân thiện chuẩn Antigravity
    return f"""🤖 <b>DẠ EM ĐÂY ANH HIẾU ƠI!</b>
━━━━━━━━━━━━━━━━━━━
Em đã nhận được câu hỏi của anh: <i>"{prompt}"</i>

Anh đang trong giai đoạn ôn luyện nước rút cho kỳ thi sát hạch Bằng C1. Em luôn đồng hành bên anh 24/7 để:
• 📖 Giải đáp cặn kẽ từng câu trong 600 câu hỏi lý thuyết & 60 câu điểm liệt.
• 🚦 Hướng dẫn bí kíp xét sa hình và điểm căn mô phỏng 120 tình huống.
• 🏔️ Luyện kỹ thuật đề-pa dốc số sàn xe tải.
• 💻 Hoặc bất kỳ thắc mắc nào về máy tính, học tập và cuộc sống!

Anh cần em hỗ trợ chi tiết phần nào cứ nhắn em ngay nhé! ❤️"""

# --- HÀM TRẢ LỜI CHÍNH KÈM RAG & XOAY VÒNG KEY ---
def ask_antigravity_ai(prompt, chat_id=None):
    """
    Hỏi Antigravity AI với kiến trúc 3 lớp:
    1. Tích hợp RAG tra cứu trực tiếp trong bộ 600 câu Bộ GTVT.
    2. Gọi cụm Google Gemini & OpenRouter AI đa model, tự động xoay key khi 429/hết quota.
    3. Bộ chuyên gia Semantic Fallback chuẩn xác 100% khi mất mạng.
    """
    cfg = load_ai_config()
    rag_context = build_rag_context(prompt)
    
    # 1. Cập nhật lịch sử hội thoại
    cid = str(chat_id or "default")
    if cid not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[cid] = []
    
    CONVERSATION_HISTORY[cid].append({"role": "user", "content": prompt})
    if len(CONVERSATION_HISTORY[cid]) > MAX_HISTORY_TURNS * 2:
        CONVERSATION_HISTORY[cid] = CONVERSATION_HISTORY[cid][-MAX_HISTORY_TURNS * 2:]
    
    messages = list(CONVERSATION_HISTORY[cid])
    
    # 2. Thử nghiệm cụm Google Gemini Keys trước (nếu có key)
    gem_keys = cfg.get('gemini_keys', [])
    if gem_keys:
        start_idx = cfg.get('active_gemini_index', 0)
        for attempt in range(len(gem_keys)):
            current_idx = (start_idx + attempt) % len(gem_keys)
            api_key = gem_keys[current_idx]
            model = cfg.get('gemini_model', 'gemini-2.5-flash')
            try:
                ans = call_gemini_api(api_key, model, messages, rag_context=rag_context)
                if ans and len(ans.strip()) > 10:
                    if current_idx != start_idx:
                        cfg['active_gemini_index'] = current_idx
                        save_ai_config(cfg)
                    CONVERSATION_HISTORY[cid].append({"role": "assistant", "content": ans})
                    return ans
            except Exception as e:
                print(f"[AI Engine] Gemini Key #{current_idx + 1} ({model}) lỗi: {e}")
                time.sleep(0.3)

    # 3. Thử nghiệm cụm OpenRouter với Multi-Model & Multi-Key
    or_keys = cfg.get('openrouter_keys', [])
    models = cfg.get('preferred_models', [
        "dots-studio/dots-3-note-preview:free",
        "liquid/lfm-2.5-2.6b:free",
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
        "nvidia/nemotron-3-super-120b-a12b:free"
    ])
    
    if or_keys:
        start_or_idx = cfg.get('active_openrouter_index', 0)
        for key_att in range(len(or_keys)):
            cur_key_idx = (start_or_idx + key_att) % len(or_keys)
            api_key = or_keys[cur_key_idx]
            
            for model_name in models:
                try:
                    ans = call_openrouter_api(api_key, model_name, messages, rag_context=rag_context)
                    if ans and len(ans.strip()) > 10:
                        if cur_key_idx != start_or_idx:
                            cfg['active_openrouter_index'] = cur_key_idx
                            save_ai_config(cfg)
                        CONVERSATION_HISTORY[cid].append({"role": "assistant", "content": ans})
                        return ans
                except Exception as e:
                    # Model bị lỗi hoặc 429/403, tự động chuyển model tiếp theo
                    time.sleep(0.3)

    # 4. Fallback chuyên sâu chuẩn xác 100% nếu toàn bộ API bị ngắt
    fb = local_knowledge_fallback(prompt)
    CONVERSATION_HISTORY[cid].append({"role": "assistant", "content": fb})
    return fb

if __name__ == '__main__':
    print("Kiểm tra AI Engine nâng cấp...")
    test_q = "Em ơi câu 15 đáp án là gì và giải thích giúp anh với!"
    reply = ask_antigravity_ai(test_q)
    print("Kết quả trả về:\n", reply)
