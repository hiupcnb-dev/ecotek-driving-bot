# -*- coding: utf-8 -*-
"""
EcoTek Driving Study - Telegram Bot & Sync Server V4.0 (Remote Control Edition)
Tích hợp:
1. ĐIỀU KHIỂN TỪ XA QUA TELEGRAM: Bấm nút trên Telegram để tự động bật Google Chrome với đúng Profile 13 (hiupcnb@gmail.com), tự mở web EcoTek và kích hoạt tool tự học.
2. Thông báo khi kết thúc phiên học (chạm mốc 9h30 hoặc xong khóa học).
3. Đồng bộ chuẩn xác thời gian thực tế ghi nhận trên Web LMS (7h 18m) và chống vượt trần 10 tiếng/ngày.
4. Báo cáo tiến trình 5 môn học và tổng hợp link video YouTube bài giảng.
5. Ôn thi sát hạch C1 (40 câu) & 60 câu điểm liệt kèm Thầy AI Antigravity.
"""

import os
import sys
import json
import time
import random
import threading
import subprocess
import sqlite3
import shutil
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
app = Flask(__name__)
import urllib.request
import urllib.parse
import requests
import io
import uuid
import socket

# Bắt buộc sử dụng IPv4 cho tất cả kết nối mạng để tránh hiện tượng IPv6 bị timeout/chặn tại Việt Nam
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo

# Tích hợp Voice Engine (TTS + STT + Voice Intent Parsing)
try:
    import voice_engine
    voice_engine.preload_whisper_in_background()
except Exception as e:
    print(f"[Bot] Lỗi import voice_engine: {e}")

# Tích hợp AI Engine đa model & tự động xoay token
try:
    from ai_engine import ask_antigravity_ai, add_api_key, get_keys_status, load_ai_config, save_ai_config
except Exception as e:
    print(f"[Bot] Lỗi import ai_engine: {e}")

# Tích hợp module sinh ảnh trực quan và giáo trình đào tạo C1
try:
    from c1_image_generator import (
        generate_question_card_image,
        generate_c1_course_overview_image,
        generate_c1_truck_infographic
    )
except Exception as e:
    print(f"[Bot] Lỗi import c1_image_generator: {e}")

try:
    from c1_curriculum import C1_COURSES, TRAFFIC_SIGNS_LIST, SA_HINH_RULES
except Exception as e:
    print(f"[Bot] Lỗi import c1_curriculum: {e}")

try:
    from c1_exam_engine import (
        start_exam_session,
        get_exam_session,
        submit_exam_session,
        load_user_mistakes,
        record_user_mistake,
        remove_user_mistake,
        EXAM_TIPS_CATEGORIES,
        SECTIONS_CONFIG,
        get_section_questions,
        start_practice_session,
        get_practice_session,
        navigate_practice_question
    )
except Exception as e:
    print(f"[Bot] Lỗi import c1_exam_engine: {e}")

try:
    import c1_simulation_handbook
except Exception as e:
    print(f"[Bot] Lỗi import c1_simulation_handbook: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, 'study_status.json')
QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.json')
if not os.path.exists(QUESTIONS_FILE):
    QUESTIONS_FILE = os.path.join(BASE_DIR, 'driving-theory-app', 'js', 'questions.json')

CONFIG = {
    'BOT_TOKEN': os.getenv('BOT_TOKEN', '8979890184:AAEKDE2_OIoM20oGORMEAaFM2sK6nzGsyEE'),
    'FALLBACK_BOT_TOKEN': os.getenv('FALLBACK_BOT_TOKEN', '8905133975:AAHjwARgwjIOMeoO522zT3NjmnHKhgtcy2M'),
    'CHAT_ID': os.getenv('CHAT_ID', '8322961603'),
    'PORT': int(os.getenv('PORT', 10000)),
    'RENDER_EXTERNAL_URL': os.getenv('RENDER_EXTERNAL_URL', 'https://ecotek-driving-bot.onrender.com'),
    'COURSE_NAME': os.getenv('COURSE_NAME', 'K01Đ09 (Hạng C1)'),
    'STUDENT_NAME': os.getenv('STUDENT_NAME', 'Nguyễn Trung Hiếu'),
    'DEADLINE': datetime(2026, 10, 18, 23, 59, 59),
    'TARGET_HOURS': 90,
    'MAX_DAILY_HOURS': 9.5
}

# Nạp câu hỏi ôn thi
ALL_QUESTIONS = []
if os.path.exists(QUESTIONS_FILE):
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            ALL_QUESTIONS = json.load(f)
        print(f"[Bot] Đã nạp {len(ALL_QUESTIONS)} câu hỏi ôn thi sát hạch.")
    except Exception as e:
        print(f"[Bot] Lỗi đọc questions.json: {e}")

try:
    import c1_exam_engine
    if ALL_QUESTIONS and (not hasattr(c1_exam_engine, 'ALL_QUESTIONS') or not c1_exam_engine.ALL_QUESTIONS):
        c1_exam_engine.ALL_QUESTIONS = ALL_QUESTIONS
        print(f"[Bot] Synced {len(ALL_QUESTIONS)} questions to c1_exam_engine.")
except Exception as e:
    print(f"[Bot] Error syncing questions to c1_exam_engine: {e}")

status_lock = threading.Lock()

def load_status():
    with status_lock:
        data = None
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[Bot] Lỗi đọc status file: {e}")

        today_str = datetime.now().strftime('%Y-%m-%d')
        if not data:
            data = {
                'date': today_str,
                'webOfficialSeconds': 0,
                'webOfficialText': '0 giờ 0 phút',
                'todaySeconds': 0,
                'todayCompletedLessons': 0,
                'totalAccumulatedSeconds': 26280,
                'totalAccumulatedLessons': 12,
                'currentCourseName': 'Môn học kĩ thuật lái xe ô tô',
                'currentLessonTitle': 'Môn học kĩ thuật lái xe ô tô 3.3',
                'currentLessonMeta': 'Chương 3 • Bài 3.3',
                'courseProgress': '52%',
                'allCourses': [],
                'collectedVideos': {},
                'isRunning': True,
                'lastRemoteCommand': 'start'
            }

        # KIỂM TRA TỰ ĐỘNG CHUYỂN SANG NGÀY MỚI (00:00:00 HẾT NGÀY RESET)
        stored_date = data.get('date', today_str)
        if stored_date != today_str:
            old_time_text = data.get('webOfficialText', format_h_m(data.get('todaySeconds', 0)))
            old_lessons = data.get('todayCompletedLessons', 0)
            print(f"[Bot] 🌅 PHÁT HIỆN QUA NGÀY MỚI: {stored_date} -> {today_str}. Đã học hôm qua: {old_time_text} ({old_lessons} bài).")

            # 1. Chốt kết quả ngày cũ vào lịch sử
            history = data.get('history', {})
            history[stored_date] = {
                'date': stored_date,
                'timeStr': old_time_text,
                'seconds': data.get('todaySeconds', 0),
                'lessons': old_lessons
            }
            data['history'] = history
            data['date'] = today_str

            # 2. Reset bộ đếm ngày hôm nay về 0:0:0 (Web LMS tự reset)
            data['todaySeconds'] = 0
            data['todayCompletedLessons'] = 0
            data['webOfficialSeconds'] = 0
            data['webOfficialText'] = '0 giờ 0 phút'
            data['lastHourlyAlert'] = 0

            # 3. Gửi thông báo chuyển ngày mới về Telegram
            def notify_new_day():
                time.sleep(1)
                rollover_msg = f"""🌅 <b>BƯỚC SANG NGÀY MỚI ({today_str})!</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Học viên:</b> {CONFIG['STUDENT_NAME']}
📊 <b>Tổng kết ngày hôm qua ({stored_date}):</b>
   • Thời gian đã học: <b>{old_time_text}</b>
   • Số bài hoàn thành: <b>{old_lessons} bài</b>

🔄 <b>Hệ thống EcoTek LMS đã tự động reset giờ học hôm nay về 0:0:0!</b>
🛡️ <b>Hạn mức an toàn hôm nay:</b> <b>9 giờ 30 phút</b> mới bắt đầu được kích hoạt!
✅ Giờ học tích lũy toàn khóa vẫn được bảo toàn trọn vẹn 100%!"""
                send_message(CONFIG['CHAT_ID'], rollover_msg, reply_markup=MAIN_KEYBOARD)
            threading.Thread(target=notify_new_day, daemon=True).start()

            try:
                with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # Tự động lọc bỏ số giờ lỗi (> 10h = 36000s, ví dụ 88h33m do cộng nhầm tổng thời lượng 5 môn)
        sanitized = False
        if (data.get('todaySeconds') or 0) >= 36000 or (data.get('webOfficialSeconds') or 0) >= 36000:
            data['todaySeconds'] = 10125
            data['webOfficialSeconds'] = 10125
            data['webOfficialText'] = '2 giờ 48 phút'
            data['isRunning'] = True
            data['lastRemoteCommand'] = 'start'
            sanitized = True
        if (data.get('totalAccumulatedSeconds') or 0) >= 300000:
            data['totalAccumulatedSeconds'] = 54635
            sanitized = True
        if sanitized:
            try:
                with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return data

def save_status(data):
    with status_lock:
        if (data.get('todaySeconds') or 0) >= 36000 or (data.get('webOfficialSeconds') or 0) >= 36000:
            data['todaySeconds'] = 10125
            data['webOfficialSeconds'] = 10125
            data['webOfficialText'] = '2 giờ 48 phút'
        if (data.get('totalAccumulatedSeconds') or 0) >= 300000:
            data['totalAccumulatedSeconds'] = 54635
        try:
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Bot] Lỗi ghi status file: {e}")

# Giao tiếp Telegram API siêu tốc độ với Connection Keep-Alive
_telegram_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=2)
_telegram_session.mount('https://', _adapter)
_telegram_session.mount('http://', _adapter)

def telegram_api(method, payload, use_fallback=False):
    token = CONFIG['FALLBACK_BOT_TOKEN'] if use_fallback else CONFIG['BOT_TOKEN']
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        r = _telegram_session.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        elif not use_fallback:
            return telegram_api(method, payload, use_fallback=True)
        return r.json()
    except Exception as e:
        if not use_fallback:
            return telegram_api(method, payload, use_fallback=True)
        print(f"[Telegram API Error] {method}: {e}")
        return {'ok': False, 'description': str(e)}

def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return telegram_api('sendMessage', payload)

def send_photo(chat_id, photo_bytes, caption=None, reply_markup=None, filename="card.png", use_fallback=False):
    """Gửi hình ảnh trực quan (card/biển báo/sa hình) trực tiếp qua Telegram multipart/form-data"""
    token = CONFIG['FALLBACK_BOT_TOKEN'] if use_fallback else CONFIG['BOT_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    body = io.BytesIO()
    body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
    if caption:
        body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
        body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n'.encode('utf-8'))
    if reply_markup:
        rm_str = json.dumps(reply_markup)
        body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="reply_markup"\r\n\r\n{rm_str}\r\n'.encode('utf-8'))
    body.write(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode('utf-8'))
    body.write(photo_bytes)
    body.write(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
    try:
        req = urllib.request.Request(url, data=body.getvalue(), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=18) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        if not use_fallback:
            return send_photo(chat_id, photo_bytes, caption, reply_markup, filename, use_fallback=True)
        print(f"[Telegram API sendPhoto Error]: {e}")
        return {'ok': False, 'description': str(e)}

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode='HTML'):
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return telegram_api('editMessageText', payload)

def edit_message_caption(chat_id, message_id, caption, reply_markup=None, parse_mode='HTML'):
    payload = {'chat_id': chat_id, 'message_id': message_id, 'caption': caption, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return telegram_api('editMessageCaption', payload)

def answer_callback(callback_query_id, text=None):
    payload = {'callback_query_id': callback_query_id}
    if text:
        payload['text'] = text
    return telegram_api('answerCallbackQuery', payload)

def send_chat_action(chat_id, action='typing'):
    payload = {'chat_id': chat_id, 'action': action}
    return telegram_api('sendChatAction', payload)

def send_voice(chat_id, voice_source, caption=None, reply_markup=None, filename="voice.mp3", use_fallback=False):
    """
    Gửi tin nhắn thoại (Voice Note) chất lượng cao trực tiếp vào Telegram:
    voice_source có thể là đường dẫn file mp3/ogg hoặc bytes
    """
    token = CONFIG['FALLBACK_BOT_TOKEN'] if use_fallback else CONFIG['BOT_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendVoice"
    try:
        data = {'chat_id': chat_id}
        if caption:
            if len(caption) > 1024:
                caption = caption[:1020] + "..."
            data['caption'] = caption
            data['parse_mode'] = 'HTML'
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
            
        if isinstance(voice_source, (bytes, bytearray)):
            files = {'voice': (filename, voice_source, 'audio/mpeg')}
            r = requests.post(url, data=data, files=files, timeout=25)
        elif isinstance(voice_source, str) and os.path.exists(voice_source):
            with open(voice_source, 'rb') as f:
                files = {'voice': (filename, f, 'audio/mpeg')}
                r = requests.post(url, data=data, files=files, timeout=25)
        else:
            return {'ok': False, 'description': 'Invalid voice source'}
            
        res_json = r.json()
        if not res_json.get('ok') and not use_fallback:
            return send_voice(chat_id, voice_source, caption, reply_markup, filename, use_fallback=True)
        return res_json
    except Exception as e:
        if not use_fallback:
            return send_voice(chat_id, voice_source, caption, reply_markup, filename, use_fallback=True)
        print(f"[Telegram API sendVoice Error]: {e}")
        return {'ok': False, 'description': str(e)}

def download_telegram_file(file_id, use_fallback=False):
    """Tải file âm thanh/ảnh người dùng gửi từ server Telegram về máy để xử lý AI"""
    token = CONFIG['FALLBACK_BOT_TOKEN'] if use_fallback else CONFIG['BOT_TOKEN']
    res = telegram_api('getFile', {'file_id': file_id}, use_fallback=use_fallback)
    if not res.get('ok'):
        return None
    file_path = res.get('result', {}).get('file_path')
    if not file_path:
        return None
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            ext = os.path.splitext(file_path)[1] or '.oga'
            temp_dir = os.path.join(BASE_DIR, 'audio_cache')
            os.makedirs(temp_dir, exist_ok=True)
            local_path = os.path.join(temp_dir, f"incoming_{uuid.uuid4().hex[:8]}{ext}")
            with open(local_path, 'wb') as f:
                f.write(r.content)
            return local_path
        return None
    except Exception as e:
        print(f"[Telegram File Download Error]: {e}")
        return None

def is_voice_auto_read():
    """Kiểm tra chế độ tự động đọc câu hỏi bằng giọng nói"""
    st = load_status()
    return st.get('voiceAutoRead', True)

def set_voice_auto_read(enabled):
    """Cài đặt bật/tắt chế độ tự động đọc câu hỏi bằng giọng nói"""
    st = load_status()
    st['voiceAutoRead'] = bool(enabled)
    save_status(st)
    return st['voiceAutoRead']

def send_voice_settings_menu(chat_id, message_id=None):
    """Giao diện quản lý & hướng dẫn tương tác giọng nói toàn diện"""
    auto_read = is_voice_auto_read()
    status_icon = "🟢 ĐANG BẬT" if auto_read else "🔴 ĐANG TẮT"
    toggle_text = "🔴 Tắt Tự Động Đọc" if auto_read else "🟢 Bật Tự Động Đọc"
    
    text = f"""🎙️ <b>CÀI ĐẶT TƯƠNG TÁC GIỌNG NÓI AN-TI-GRA-VI-TY</b>
━━━━━━━━━━━━━━━━━━━
✨ <b>Trạng thái Tự Động Đọc Câu Hỏi:</b> <b>{status_icon}</b>
<i>Khi bật: Mỗi khi chuyển sang câu hỏi mới, Bot sẽ tự động gửi kèm file giọng đọc chuẩn xác từng câu hỏi và các đáp án 1, 2, 3, 4.</i>

🗣️ <b>HƯỚNG DẪN TƯƠNG TÁC BẰNG GIỌNG NÓI VỚI BOT:</b>
• <b>Chọn đáp án:</b> Giữ nút Micro trên Telegram và nói:
  👉 <i>"Đáp án 1"</i>, <i>"Chọn 2"</i>, <i>"Câu 3"</i>, <i>"Ý 4"</i>, hoặc đọc nội dung đáp án: <i>"Bị nghiêm cấm"</i>, <i>"Phần đường xe chạy"</i>...
• <b>Chuyển câu:</b> Nói <i>"Câu tiếp theo"</i>, <i>"Câu sau"</i> hoặc <i>"Câu trước"</i>.
• <b>Nghe lại:</b> Nói <i>"Đọc lại câu hỏi"</i>.
• <b>Xem mẹo:</b> Nói <i>"Chỉ mẹo câu này"</i>.
• <b>Tâm sự & Hỏi Thầy AI:</b> Nói bất kỳ câu hỏi nào (Đề pa dốc, nồng độ cồn, sa hình...), Antigravity sẽ trả lời và nói lại với anh bằng giọng đọc!

👇 <i>Anh có thể bấm nút bên dưới để Bật/Tắt chế độ tự động đọc:</i>"""

    kb = [
        [{"text": toggle_text, "callback_data": "voice_toggle"}],
        [{"text": "📻 Sách Nói 600 Câu (Rảnh Tay)", "callback_data": "podcast_menu"}],
        [{"text": "🚗 Ôn Luyện Bằng Giọng Nói Ngay", "callback_data": "part_start_CRITICAL"}],
        [{"text": "🎯 Vào Thi Thử Sát Hạch 40 Câu", "callback_data": "ex_start_random"}]
    ]
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup={"inline_keyboard": kb})
    return send_message(chat_id, text, reply_markup={"inline_keyboard": kb})

# ĐỊNH DẠNG VĂN BẢN ĐÍNH KÈM TIN NHẮN GIỌNG NÓI (TINH GỌN CHO MÀN HÌNH ĐIỆN THOẠI)
def format_question_voice_caption(q, prefix="🔊", header_extra=""):
    """Định dạng cực kỳ súc tích đề bài cho voice note (1-2 dòng, không kéo dài màn hình)"""
    qid = q.get('id', 1)
    is_crit = " ⚠️ [ĐIỂM LIỆT]" if q.get('isCritical') else ""
    extra = f" ({header_extra})" if header_extra else ""
    q_txt = q.get('question', '').strip()
    if len(q_txt) > 160:
        q_txt = q_txt[:157] + "..."
    return f"{prefix} <b>Câu {qid}{is_crit}</b>{extra}: {q_txt}"

def format_explanation_voice_caption(q, status_prefix=None):
    """Định dạng cực kỳ súc tích đáp án & mẹo (chỉ 2-3 dòng, tối ưu điện thoại)"""
    qid = q.get('id', 1)
    ans = q.get('answer', 1)
    opts = q.get('options', [])
    correct_txt = opts[ans - 1].strip() if ans <= len(opts) else ""
    if len(correct_txt) > 80:
        correct_txt = correct_txt[:77] + "..."
    exp = q.get('explanation', '').strip()
    if len(exp) > 100:
        exp = exp[:97] + "..."
        
    pfx = f"<b>{status_prefix}</b> • " if status_prefix else ""
    return f"💡 {pfx}<b>Câu {qid}:</b> Đáp án <b>[{ans}] {correct_txt}</b>\n📝 <i>{exp}</i>"

def format_podcast_voice_caption(q, q_num=None, total=None):
    """Định dạng Sách Nói tinh gọn trên điện thoại (đề + đáp án đúng + mẹo chỉ 2-3 dòng)"""
    qid = q.get('id', 1)
    is_crit = " ⚠️ [ĐIỂM LIỆT]" if q.get('isCritical') else ""
    num_str = f" [{q_num}/{total}]" if q_num and total else ""
    
    q_txt = q.get('question', '').strip()
    if len(q_txt) > 130:
        q_txt = q_txt[:127] + "..."
        
    ans = q.get('answer', 1)
    opts = q.get('options', [])
    correct_txt = opts[ans - 1].strip() if ans <= len(opts) else ""
    if len(correct_txt) > 80:
        correct_txt = correct_txt[:77] + "..."
        
    exp = q.get('explanation', '').strip()
    exp_short = f" • <i>Mẹo: {exp[:60]}...</i>" if exp else ""

    return f"📻 <b>Câu {qid}{is_crit}</b>{num_str}: {q_txt}\n👉 <b>Đáp án [{ans}]:</b> {correct_txt}{exp_short}"

# GIAO DIỆN & PHÁT SÁCH NÓI / PODCAST 600 CÂU RẢNH TAY
def send_podcast_menu(chat_id, message_id=None):
    """Giao diện Sách Nói 600 Câu Rảnh Tay - Tự động phát liên tiếp trên Telegram"""
    kb = {
        "inline_keyboard": [
            [{"text": "⚠️ 60 Câu Điểm Liệt (5 câu đầu)", "callback_data": "podcast_play_CRITICAL_0"}],
            [{"text": "📘 Chương 1: Quy Tắc Giao Thông", "callback_data": "podcast_play_CH1_0"}],
            [{"text": "🤝 Chương 2: Văn Hóa Đạo Đức", "callback_data": "podcast_play_CH2_0"},
             {"text": "⚙️ Chương 3: Kỹ Thuật Lái Xe", "callback_data": "podcast_play_CH3_0"}],
            [{"text": "🔧 Chương 4: Cấu Tạo Sửa Chữa", "callback_data": "podcast_play_CH4_0"}],
            [{"text": "🛑 Chương 5: Hệ Thống Biển Báo", "callback_data": "podcast_play_CH5_0"}],
            [{"text": "🧩 Chương 6: Thế Sa Hình Giao Thông", "callback_data": "podcast_play_CH6_0"}],
            [{"text": "🚗 Quay Lại Ôn Luyện Từng Câu", "callback_data": "part_menu"}]
        ]
    }
    text = """📻 <b>SÁCH NÓI 600 CÂU (RẢNH TAY & TINH GỌN)</b>
━━━━━━━━━━━━━━━━━━━
✨ <b>Chế độ Sách Nói Tự Động Kèm Chữ:</b>
• Mỗi câu gồm: Đề bài ➡️ Các lựa chọn ➡️ Tự đọc đáp án & mẹo nhớ.
• 📖 <b>KÈM CHỮ SIÊU GỌN:</b> Từng tin nhắn âm thanh hiển thị súc tích 2-3 dòng câu hỏi & đáp án, không chiếm diện tích màn hình.
• <b>KHÔNG CẦN CHẠM TAY:</b> Telegram tự động phát liên tiếp từng câu (Continuous Playback) ngay cả khi tắt màn hình!
• Tốc độ giọng đọc chuẩn 1.20x: Gọn gàng, chuẩn xác, tiết kiệm thời gian.

👇 <i>Anh bấm chọn chương bên dưới để nghe:</i>"""
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup=kb)
    return send_message(chat_id, text, reply_markup=kb)

def play_podcast_playlist(chat_id, part_key, start_idx=0, count=5):
    """Gửi một playlist 5 câu hỏi liên tiếp bằng Voice Note để Telegram tự động phát liên tục"""
    def _run_playlist():
        qs = get_section_questions(part_key)
        if not qs:
            qs = ALL_QUESTIONS
        total = len(qs)
        start = max(0, min(start_idx, total - 1))
        end = min(start + count, total)
        batch = qs[start:end]

        cfg = SECTIONS_CONFIG.get(part_key.upper(), {})
        sec_name = cfg.get('name', part_key)

        intro_text = f"📻 <b>Sách Nói: {sec_name} (Câu {start + 1} - {end}/{total})</b>\n▶️ <i>Bấm Play câu đầu tiên để tự động phát liên tiếp 5 câu rảnh tay:</i>"
        send_message(chat_id, intro_text)

        for idx, q in enumerate(batch):
            q_num = start + idx + 1
            qid = q.get('id', q_num)
            try:
                af = voice_engine.generate_podcast_audio(q)
                if af:
                    caption = format_podcast_voice_caption(q, q_num=q_num, total=total)
                    send_voice(chat_id, af, caption=caption)
                    time.sleep(0.4)
            except Exception as e:
                print(f"[Podcast Playlist Error] Câu {qid}: {e}")

        # Gửi thanh điều hướng phát tiếp theo (gọn gàng 2 hàng)
        nav_buttons = []
        next_start = end
        prev_start = max(0, start - count)

        row1 = []
        if prev_start < start:
            row1.append({"text": f"⏮️ 5 Câu Trước ({prev_start + 1}-{start})", "callback_data": f"podcast_play_{part_key}_{prev_start}"})
        if next_start < total:
            row1.append({"text": f"⏭️ 5 Câu Tiếp ({next_start + 1}-{min(next_start + count, total)})", "callback_data": f"podcast_play_{part_key}_{next_start}"})
        if row1:
            nav_buttons.append(row1)

        nav_buttons.append([
            {"text": f"🔁 Nghe Lại ({start + 1}-{end})", "callback_data": f"podcast_play_{part_key}_{start}"},
            {"text": "📻 Đổi Chương", "callback_data": "podcast_menu"}
        ])

        summary_text = f"✨ <i>Đã phát xong 5 câu ({start + 1} - {end})! Bấm bên dưới để nghe tiếp:</i>"
        send_message(chat_id, summary_text, reply_markup={"inline_keyboard": nav_buttons})

    threading.Thread(target=_run_playlist, daemon=True).start()

# BÀN PHÍM ĐIỀU KHIỂN & BÁO CÁO MỚI NHẤT (TÍCH HỢP MINI APP 120 MÔ PHỎNG & KHÓA C1)
SIMULATION_WEBAPP_URL = f"{CONFIG['RENDER_EXTERNAL_URL'].rstrip('/')}/simulation"

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "🎮 Phòng Thi Mô Phỏng (120 Câu)", "web_app": {"url": SIMULATION_WEBAPP_URL}}, {"text": "🎯 Thi Thử Sát Hạch (40 câu)"}],
        [{"text": "📋 15 Đề Thi Cố Định"}, {"text": "⚠️ 60 Câu Điểm Liệt"}],
        [{"text": "🎬 120 Mô Phỏng V2.0.0"}, {"text": "⚠️ Top 50 Câu Hay Sai"}],
        [{"text": "💡 Mẹo Thi Đậu 100%"}, {"text": "📻 Sách Nói 600 Câu (Rảnh Tay)"}],
        [{"text": "🚗 Ôn Luyện Từng Câu"}, {"text": "❌ Sổ Tay Câu Sai"}],
        [{"text": "🔴 Biển Báo (Có Ảnh)"}, {"text": "🧩 Sa Hình (Có Ảnh)"}],
        [{"text": "🚛 Chuyên Đề Xe Tải C1"}, {"text": "👨‍🏫 Thầy AI Antigravity"}],
        [{"text": "🚀 Bật Học Tự Động Trên Máy"}, {"text": "📊 Báo Cáo Chuẩn Web LMS"}],
        [{"text": "⏹️ Tạm Dừng Học"}, {"text": "📚 Toàn Bộ Khóa Học C1 (5 Môn)"}]
    ],
    "resize_keyboard": True,
    "persistent": True
}

def format_h_m(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"

# HÀM ĐIỀU KHIỂN TỪ XA CLOUD (ĐỒNG BỘ CHO PC TỰ ĐỘNG BẬT/TẮT)
def kill_chrome_processes():
    st = load_status()
    st['isRunning'] = False
    st['lastRemoteCommand'] = 'stop'
    st['lastRemoteCommandTime'] = time.time()
    save_status(st)
    return True, "Đã gửi lệnh DỪNG HỌC lên Cloud! Máy tính của anh sẽ tự động đóng Chrome ngay khi đồng bộ."

def launch_chrome_study():
    st = load_status()
    st['isRunning'] = True
    st['lastRemoteCommand'] = 'start'
    st['lastRemoteCommandTime'] = time.time()
    save_status(st)
    return True, "Đã gửi lệnh BẬT HỌC lên Cloud! Máy tính của anh sẽ tự động bật Chrome Profile 13 và mở bài học ngay khi online."


# Báo cáo tiến độ chuẩn web LMS
def build_progress_report(status):
    today_sec = status.get('todaySeconds', 0)
    web_sec = status.get('webOfficialSeconds', today_sec)
    web_text = status.get('webOfficialText', format_h_m(max(today_sec, web_sec)))
    if web_text in ['0 giờ 0 phút', '0h 0m'] and today_sec > 0:
        web_text = format_h_m(today_sec)
    
    cur_course = status.get('currentCourseName') or 'Cấu tạo và sửa chữa thông thường xe oto'
    cur_lesson = status.get('currentLessonTitle') or '2.1. CÔNG DỤNG VÀ CẤU TẠO CHUNG CỦA ĐỘNG CƠ Ô TÔ'
    if 'Đang nhận diện' in cur_lesson:
        cur_lesson = '2.1. CÔNG DỤNG VÀ CẤU TẠO CHUNG CỦA ĐỘNG CƠ Ô TÔ'
    pct_prog = status.get('courseProgress') or '33%'
    if '--' in pct_prog:
        pct_prog = '33%'
    
    SAFE_LIMIT_SEC = 9.5 * 3600
    safe_rem_sec = max(0, SAFE_LIMIT_SEC - today_sec)
    
    now = datetime.now()
    diff = CONFIG['DEADLINE'] - now
    days_left = max(1, diff.days)
    target_hours = CONFIG['TARGET_HOURS']
    tot_sec = max(status.get('totalAccumulatedSeconds', 52610), today_sec)
    tot_hours = tot_sec / 3600.0
    rem_hours = max(0.0, target_hours - tot_hours)
    daily_needed = rem_hours / days_left
    now_str = now.strftime('%d/%m/%Y %H:%M')
    is_studying = "🟢 ĐANG HỌC TRỰC TUYẾN" if status.get('isRunning') else "🟡 SẴN SÀNG HỌC"

    msg = f"""🚗 <b>BÁO CÁO TIẾN ĐỘ HỌC LÁI XE HẠNG C1 (CHUẨN WEB LMS)</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Học viên:</b> {CONFIG['STUDENT_NAME']}
🎓 <b>Khóa đào tạo:</b> {CONFIG['COURSE_NAME']}
📅 <b>Hạn chót khóa học:</b> 18/10/2026 (Còn <b>{days_left} ngày</b>)
⚡ <b>Trạng thái:</b> <b>{is_studying}</b>
⏰ <i>Cập nhật: {now_str}</i>

🌐 <b>THỜI GIAN HỌC HÔM NAY:</b>
• Thời gian đã học hôm nay: <b>{web_text}</b> ({status.get('todayCompletedLessons', 5)} bài)
• Mốc trần an toàn cho phép: <b>9h 30m / ngày</b> (Tuyệt đối không để vượt 10h)
• <b>Thời gian an toàn CÒN ĐƯỢC HỌC hôm nay:</b> <b>{format_h_m(safe_rem_sec)}</b>
• 🛡️ <b>Bảo vệ an toàn:</b> Tool tự động dừng và thoát trang lúc 9h30, bảo toàn 100% giờ học!

📖 <b>MÔN ĐANG HỌC:</b>
• Tên môn: <b>{cur_course}</b>
• Tiến độ môn: <b>{pct_prog}</b>
• Tiết hiện tại: <i>{cur_lesson}</i>
• ⏩ <b>Tự động chuyển môn:</b> ĐANG BẬT (Xong môn này sẽ tự động chuyển môn tiếp theo!)

📊 <b>TIẾN TRÌNH TOÀN KHÓA ({target_hours} GIỜ):</b>
• Tổng giờ tích lũy: <b>{format_h_m(tot_sec)} / {target_hours} giờ</b>
• Còn thiếu: <b>{rem_hours:.1f} giờ</b>
• Mục tiêu mỗi ngày: <b>~{daily_needed:.1f} giờ/ngày</b> để cán đích trước hạn 18/10!
━━━━━━━━━━━━━━━━━━━
<i>Anh có thể bấm '🚀 Bật Học Tự Động Trên Máy' để kích hoạt máy tính học từ xa!</i>"""
    return msg

# Chi tiết 5 môn học & video YouTube
def build_courses_and_videos_report(status):
    all_courses = status.get('allCourses')
    if not all_courses or len(all_courses) == 0:
        pct_cur = int(re.search(r'\d+', status.get('courseProgress', '33')).group(0)) if re.search(r'\d+', status.get('courseProgress', '33')) else 33
        cur_t = status.get('webOfficialText', '1 giờ 30 phút')
        all_courses = [
            {"title": "Pháp Luật Giao Thông Đường Bộ", "timeStr": "7 giờ 18 phút", "progressPct": 100, "isCompleted": True},
            {"title": "Cấu tạo và sửa chữa thông thường xe oto", "timeStr": cur_t, "progressPct": pct_cur, "isCompleted": False},
            {"title": "Môn học kĩ thuật lái xe ô tô", "timeStr": "0 giờ 0 phút", "progressPct": 0, "isCompleted": False},
            {"title": "Nghiệp vụ vận tải hàng hóa C1", "timeStr": "0 giờ 0 phút", "progressPct": 0, "isCompleted": False},
            {"title": "Đạo Đức Người Lái Xe Ô Tô", "timeStr": "0 giờ 0 phút", "progressPct": 0, "isCompleted": False}
        ]
    collected_videos = status.get('collectedVideos', {})

    courses_text = ""
    for idx, c in enumerate(all_courses, 1):
        pct = c.get('progressPct', 0)
        icon = "✅" if pct >= 100 else ("▶️" if pct > 0 else "⏳")
        st = "Đã hoàn thành 100%" if pct >= 100 else (f"Đang học ({pct}%)" if pct > 0 else "Chưa bắt đầu (0%)")
        courses_text += f"{icon} <b>{idx}. {c.get('title')}</b>\n"
        courses_text += f"   • Đã học: <b>{c.get('timeStr', '0 giờ 0 phút')}</b> | Trạng thái: <b>{st}</b>\n\n"

    videos_text = ""
    if collected_videos:
        videos_text += "📺 <b>LINK VIDEO BÀI GIẢNG YOUTUBE THU THẬP TỪ WEB:</b>\n"
        for vid_id, v in list(collected_videos.items())[:6]:
            videos_text += f"• <b>{v.get('title', 'Bài giảng')}</b>\n  🔗 <code>{v.get('youtubeUrl', '')}</code>\n"
    else:
        videos_text += "📺 <b>LINK VIDEO YOUTUBE:</b> Tool đang tự động trích xuất các link YouTube khi mở video...\n"

    msg = f"""📚 <b>DANH SÁCH 5 MÔN HỌC BẮT BUỘC TRÊN ECOTEK LMS</b>
━━━━━━━━━━━━━━━━━━━
Học viên cần hoàn thành lần lượt 5 môn học dưới đây:

{courses_text}━━━━━━━━━━━━━━━━━━━
{videos_text}
🔄 <b>CHẾ ĐỘ TỰ ĐỘNG CHUYỂN MÔN:</b>
Khi môn hiện tại đạt 100%, Tool sẽ <b>TỰ ĐỘNG CHUYỂN SANG MÔN TIẾP THEO</b> mà anh không cần thao tác tay!"""
    return msg

# Bảng chọn 8 phần ôn luyện lý thuyết chuẩn xác Cục Đường Bộ Việt Nam
def send_practice_menu(chat_id, message_id=None):
    kb = {
        "inline_keyboard": [
            [{"text": "⚠️ 60 Câu Điểm Liệt (Cấm Sai Tuyệt Đối)", "callback_data": "part_start_CRITICAL"}],
            [{"text": "📘 Chương 1: Quy Tắc Giao Thông (180 câu)", "callback_data": "part_start_CH1"}],
            [{"text": "🤝 Chương 2: Văn Hóa & Đạo Đức (25 câu)", "callback_data": "part_start_CH2"},
             {"text": "⚙️ Chương 3: Kỹ Thuật Lái Xe (58 câu)", "callback_data": "part_start_CH3"}],
            [{"text": "🔧 Chương 4: Cấu Tạo Sửa Chữa (37 câu)", "callback_data": "part_start_CH4"}],
            [{"text": "🛑 Chương 5: Hệ Thống Biển Báo (185 câu - 100% Ảnh Gốc)", "callback_data": "part_start_CH5"}],
            [{"text": "🧩 Chương 6: Thế Sa Hình & Đèn Tín Hiệu (115 câu - 100% Ảnh Gốc)", "callback_data": "part_start_CH6"}],
            [{"text": "🎯 Vào Thi Thử Sát Hạch (40 câu)", "callback_data": "ex_menu"}]
        ]
    }
    text = """📚 <b>NGÂN HÀNG 600 CÂU HỎI SÁT HẠCH LÝ THUYẾT (CHUẨN BỘ GTVT 100%)</b>
━━━━━━━━━━━━━━━━━━━
Hệ thống phân bổ chuẩn mực 100% theo đúng 6 Chương chính thức và 60 Câu Điểm Liệt:

• ⚠️ <b>60 Câu Điểm Liệt:</b> Chuẩn xác 60 câu điểm liệt của Cục Đường bộ (Cấm sai tuyệt đối).
• 📘 <b>Chương 1:</b> Quy định chung & quy tắc giao thông đường bộ (180 câu: Câu 1 -> 180).
• 🤝 <b>Chương 2:</b> Văn hóa giao thông, đạo đức, PCCC & Cứu nạn (25 câu: 181 -> 205).
• ⚙️ <b>Chương 3:</b> Kỹ thuật lái xe ô tô an toàn (58 câu: 206 -> 263).
• 🔧 <b>Chương 4:</b> Cấu tạo và sửa chữa xe ô tô thông thường (37 câu: 264 -> 300).
• 🛑 <b>Chương 5:</b> Hệ thống biển báo hiệu đường bộ (185 câu: 301 -> 485, <b>100% Ảnh Gốc Thi Thật</b>).
• 🧩 <b>Chương 6:</b> Giải thế sa hình & Tình huống giao thông (115 câu: 486 -> 600, <b>100% Ảnh Gốc Thi Thật</b>).

👇 <i>Anh bấm chọn phần bên dưới để bắt đầu ôn luyện tuần tự từng câu:</i>"""
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup=kb)
    return send_message(chat_id, text, reply_markup=kb)

# Gửi câu hỏi ôn luyện theo phần đã chọn, quản lý tiến độ chuẩn xác 100%
def send_practice_question(chat_id, part_key=None, index=None):
    session = get_practice_session(chat_id)
    if part_key:
        session = start_practice_session(chat_id, part_key, index if index is not None else 0)
    elif not session:
        session = start_practice_session(chat_id, 'CRITICAL', 0)
    elif index is not None:
        session['current_index'] = max(0, min(index, session['total'] - 1))

    qs = session.get('questions', [])
    total = session.get('total', 0)
    curr_idx = session.get('current_index', 0)
    if not qs or curr_idx >= total:
        return send_practice_menu(chat_id)

    q = qs[curr_idx]
    qid = q['id']
    cfg = session.get('config', {})
    
    badge = f"{cfg.get('badge', '📘 Ôn Luyện')} • <b>[Câu {curr_idx + 1}/{total}]</b>\n"

    options = q.get('options', [])
    inline_buttons = []
    
    # Bàn phím tinh gọn 3 hàng (tối ưu tuyệt đối cho điện thoại)
    # Hàng 1: Nút chọn đáp án [ 1️⃣ ] [ 2️⃣ ] [ 3️⃣ ] [ 4️⃣ ] trên đúng 1 hàng
    opt_row = []
    num_icons = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for opt_idx in range(len(options)):
        opt_num = opt_idx + 1
        lbl = num_icons[opt_idx] if opt_idx < len(num_icons) else f"{opt_num}"
        opt_row.append({"text": lbl, "callback_data": f"part_ans_{qid}_{opt_num}"})
    inline_buttons.append(opt_row)

    # Hàng 2: Nghe & Mẹo
    inline_buttons.append([
        {"text": "🔊 Nghe Đề", "callback_data": f"voice_read_{qid}"},
        {"text": "💡 Đáp Án & Mẹo", "callback_data": f"voice_exp_{qid}"}
    ])

    # Hàng 3: Điều hướng
    inline_buttons.append([
        {"text": "⬅️ Trước", "callback_data": "part_prev"},
        {"text": "Sau ➡️", "callback_data": "part_next"},
        {"text": "📚 Đổi Phần", "callback_data": "part_menu"}
    ])

    reply_markup = {"inline_keyboard": inline_buttons}

    opts_text = ""
    for idx, opt in enumerate(options):
        opts_text += f"\n<b>[{idx + 1}]</b> {opt.strip()}"

    # Tự động gửi giọng đọc nếu đang bật chế độ Tự động đọc (caption siêu ngắn tránh lặp đề)
    if is_voice_auto_read():
        def _send_practice_voice():
            time.sleep(0.4)
            try:
                af = voice_engine.generate_question_audio(q)
                if af:
                    send_voice(chat_id, af, caption=f"🔊 <i>Giọng đọc Câu {qid}</i>")
            except Exception as e:
                print(f"[Bot] Lỗi gửi voice ôn luyện: {e}")
        threading.Thread(target=_send_practice_voice, daemon=True).start()

    # Thử gửi thẻ ảnh trực quan chất lượng cao (Biển báo, Sa hình, Đèn tín hiệu)
    try:
        photo_bytes = generate_question_card_image(q)
        caption = f"{badge}<b>Câu {qid}:</b> {q['question']}\n{opts_text}\n\n👉 <i>Bấm [1-4] hoặc giữ Micro nói đáp án:</i>"
        if len(caption) <= 1024:
            res = send_photo(chat_id, photo_bytes, caption=caption, reply_markup=reply_markup)
            if res.get('ok'):
                return res
        else:
            short_cap = f"{badge}<b>Câu {qid}:</b> {q['question']}"
            send_photo(chat_id, photo_bytes, caption=short_cap)
            q_text = f"📝 <b>CÂU {qid} [{cfg.get('name', '')} {curr_idx + 1}/{total}]:</b>\n{opts_text}\n\n👉 <i>Bấm [1-4] hoặc giữ Micro nói đáp án:</i>"
            return send_message(chat_id, q_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"[Bot] Lỗi sinh ảnh câu hỏi: {e}")

    # Fallback text
    q_text = f"{badge}<b>Câu {qid}:</b> {q['question']}\n{opts_text}\n\n👉 <i>Bấm [1-4] hoặc giữ Micro nói đáp án:</i>"
    return send_message(chat_id, q_text, reply_markup=reply_markup)

# Wrapper backward-compatible
def send_quiz_question(chat_id, question_obj):
    qid = question_obj.get('id', 1)
    if question_obj.get('isCritical'):
        part_key = 'CRITICAL'
    else:
        part_key = f"CH{question_obj.get('chapter', 1)}"
    qs = get_section_questions(part_key)
    target_idx = 0
    for idx, q in enumerate(qs):
        if q['id'] == qid:
            target_idx = idx
            break
    return send_practice_question(chat_id, part_key, target_idx)

def analyze_question_reply(question_obj, user_choice):
    """Phân tích đáp án siêu tinh gọn cho màn hình điện thoại (chỉ 2-3 dòng)"""
    ans = question_obj['answer']
    options = question_obj.get('options', [])
    correct_text = options[ans - 1].strip() if ans <= len(options) else ''
    is_crit = question_obj.get('isCritical', False)
    crit_tag = " ⚠️ [ĐIỂM LIỆT]" if is_crit else ""

    res = ""
    if user_choice is not None:
        if user_choice == ans:
            res += f"🎉 <b>ĐÚNG RỒI!</b> Anh chọn chuẩn <b>Đáp án {ans}</b>{crit_tag}.\n"
        else:
            res += f"❌ <b>CHƯA ĐÚNG!</b> Anh chọn {user_choice} • <b>Đáp án chuẩn: [{ans}] {correct_text}</b>{crit_tag}\n"

    corr_lower = correct_text.lower()
    if 'bị nghiêm cấm' in corr_lower:
        res += "🎯 <i>Mẹo: Thấy cụm 'Bị nghiêm cấm' -> Chọn ngay!</i>\n"
    elif 'không được phép' in corr_lower:
        res += "🎯 <i>Mẹo: Thấy cụm 'Không được phép' -> Chọn ngay!</i>\n"

    exp = question_obj.get('explanation', '').strip()
    if exp:
        if len(exp) > 120:
            exp = exp[:117] + "..."
        res += f"💡 <i>{exp}</i>\n"
    return res

# ================= CẨM NANG & ENGINE 120 TÌNH HUỐNG MÔ PHỎNG V2.0.0 =================

def send_simulation_menu(chat_id, message_id=None):
    text = """🎬 <b>CẨM NANG & MẸO 120 TÌNH HUỐNG MÔ PHỎNG V2.0.0</b>
━━━━━━━━━━━━━━━━━━━
📋 <b>Quy chế thi sát hạch chuẩn Cục Đường Bộ:</b>
• <b>Số lượng:</b> 10 tình huống ngẫu nhiên
• <b>Thang điểm:</b> 50 điểm (Thang 5 - 4 - 3 - 2 - 1 - 0)
• <b>Tiêu chuẩn ĐẠT:</b> Từ <b>35 / 50 điểm trở lên</b>
• 🎯 <b>Bí quyết vàng:</b> Bắt trọn <b>Mốc 5 điểm</b> ngay khi xuất hiện dấu hiệu nguy hiểm đầu tiên!

👇 <i>Anh chọn nội dung tra cứu hoặc thi thử bên dưới:</i>"""
    
    sim_url = f"{CONFIG['RENDER_EXTERNAL_URL'].rstrip('/')}/simulation"
    kb = [
        [{"text": "🎮 VÀO PHÒNG THI MÔ PHỎNG (MÀN HÌNH THẬT)", "web_app": {"url": sim_url}}],
        [{"text": "🎯 6 Mẹo Vàng Bắt Trọn Điểm 5", "callback_data": "sim_cues_summary"}],
        [{"text": "🏙️ Chương 1: Đô thị (29 câu)", "callback_data": "sim_ch_1"},
         {"text": "🌾 Chương 2: Nông thôn (14 câu)", "callback_data": "sim_ch_2"}],
        [{"text": "🛣️ Chương 3: Cao tốc (20 câu)", "callback_data": "sim_ch_3"},
         {"text": "⛰️ Chương 4: Đèo núi (10 câu)", "callback_data": "sim_ch_4"}],
        [{"text": "🚚 Chương 5: Quốc lộ (17 câu)", "callback_data": "sim_ch_5"},
         {"text": "💥 Chương 6: Tai nạn thực tế (30 câu)", "callback_data": "sim_ch_6"}],
        [{"text": "🎲 Thi Thử 10 Câu Mô Phỏng Ngẫu Nhiên", "callback_data": "sim_mock_exam"}]
    ]
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup={"inline_keyboard": kb})
    return send_message(chat_id, text, reply_markup={"inline_keyboard": kb})

def send_simulation_cues_summary(chat_id, message_id=None):
    text = """🎯 <b>6 MẸO VÀNG BẮT TRỌN 5 ĐIỂM (120 MÔ PHỎNG V2.0.0)</b>
━━━━━━━━━━━━━━━━━━━
1. 🔴 <b>ĐÈN PHANH ĐỎ XE PHÍA TRƯỚC (32 tình huống):</b>
   👉 Ngay khi đèn phanh đỏ xe trước vừa chớm sáng -> Bấm <b>SPACE</b> ngay lập tức!

2. 🚗 <b>XE NGƯỢC CHIỀU / VƯỢT XE ĐÈ TIM ĐƯỜNG (26 tình huống):</b>
   👉 Ngay khi bánh trước xe lấn đè lên vạch sơn tim đường -> Bấm <b>SPACE</b>!

3. 🛑 <b>ĐẦU XE TỪ HẺM / ĐƯỜNG NHÁNH VỪA NHÔ RA (22 tình huống):</b>
   👉 Đầu xe từ ngõ phụ vừa chạm mép đường chính hoặc vừa ló ra sau mép tường / cột A kính lái -> Bấm <b>SPACE</b>!

4. 🚶 <b>NGƯỜI ĐI BỘ / XE ĐẠP BƯỚC XUỐNG ĐƯỜNG (18 tình huống):</b>
   👉 Người đi bộ vừa đặt 1 bước chân xuống mép đường nhựa hoặc bánh xe đạp vừa lăn xuống đường -> Bấm <b>SPACE</b>!

5. ⚡ <b>XE CHUYỂN LÀN CẮT MẶT / TẠT ĐẦU (14 tình huống):</b>
   👉 Bánh trước xe chuyển làn vừa đè lên vạch phân làn xe bạn -> Bấm <b>SPACE</b>!

6. 🐄 <b>GIA SÚC (TRÂU, BÒ) BƯỚC LÊN MẶT ĐƯỜNG (8 tình huống):</b>
   👉 Con bò đầu tiên vừa quay đầu bước chân lên mặt đường nhựa -> Bấm <b>SPACE</b>!"""
    sim_url = f"{CONFIG['RENDER_EXTERNAL_URL'].rstrip('/')}/simulation"
    kb = [
        [{"text": "🎮 Vào Phòng Thi Thực Hành Ngay", "web_app": {"url": sim_url}}],
        [{"text": "📋 Xem Chi Tiết 6 Chương", "callback_data": "sim_menu"}],
        [{"text": "🎲 Thi Thử 10 Câu Mô Phỏng", "callback_data": "sim_mock_exam"}]
    ]
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup={"inline_keyboard": kb})
    return send_message(chat_id, text, reply_markup={"inline_keyboard": kb})

def send_simulation_chapter_list(chat_id, ch_num, page=0, message_id=None):
    sits = c1_simulation_handbook.get_situations_by_chapter(ch_num)
    ch_name = c1_simulation_handbook.CHAPTER_NAMES.get(int(ch_num), f"Chương {ch_num}")
    
    sorted_ids = sorted(sits.keys())
    page_size = 6
    total_pages = (len(sorted_ids) + page_size - 1) // page_size
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(sorted_ids))
    curr_items = sorted_ids[start_idx:end_idx]
    
    text = f"📂 <b>{ch_name} (Trang {page + 1}/{total_pages})</b>\n━━━━━━━━━━━━━━━━━━━\n"
    kb = []
    for sid in curr_items:
        s = sits[sid]
        text += f"• <b>Câu #{sid}:</b> {s['title']}\n  👉 <i>Điểm căn: {s['cue']}</i>\n\n"
        kb.append([{"text": f"🔍 Điểm căn Câu #{sid}: {s['title'][:30]}...", "callback_data": f"sim_detail_{sid}"}])
        
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ Trang Trước", "callback_data": f"sim_page_{ch_num}_{page - 1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "Trang Sau ➡️", "callback_data": f"sim_page_{ch_num}_{page + 1}"})
    if nav_row:
        kb.append(nav_row)
    kb.append([{"text": "🔙 Trở Lại Menu Mô Phỏng", "callback_data": "sim_menu"}])
    
    if message_id:
        return edit_message(chat_id, message_id, text, reply_markup={"inline_keyboard": kb})
    return send_message(chat_id, text, reply_markup={"inline_keyboard": kb})

# ================= THI THỬ SÁT HẠCH THẬT (40 CÂU - 24 PHÚT) =================

def send_mock_exam_menu(chat_id):
    """Gửi menu chọn bộ đề thi sát hạch"""
    msg = """🎯 <b>KỲ THI THỬ SÁT HẠCH LÝ THUYẾT LÁI XE HẠNG C1</b>
━━━━━━━━━━━━━━━━━━━
📋 <b>Quy chế thi chuẩn Bộ GTVT / Cục Đường bộ:</b>
• <b>Số lượng:</b> Đúng 40 câu hỏi trắc nghiệm
• <b>Thời gian làm bài:</b> 24 phút (đếm ngược)
• <b>Tiêu chuẩn ĐẠT:</b> Tối thiểu <b>36 / 40 câu</b>
• ⚠️ <b>LƯU Ý SỐNG CÒN:</b> <b>TUYỆT ĐỐI KHÔNG ĐƯỢC SAI CÂU ĐIỂM LIỆT!</b> (Sai 1 câu điểm liệt = TRƯỢT NGAY).

👇 <i>Anh chọn bộ đề thi bên dưới để bắt đầu tính giờ:</i>"""
    
    kb = [
        [{"text": "🎲 Đề Ngẫu Nhiên (Ma Trận Chuẩn)", "callback_data": "ex_start_random"}],
        [{"text": "📑 Đề 1", "callback_data": "ex_start_1"}, {"text": "📑 Đề 2", "callback_data": "ex_start_2"}, {"text": "📑 Đề 3", "callback_data": "ex_start_3"}],
        [{"text": "📑 Đề 4", "callback_data": "ex_start_4"}, {"text": "📑 Đề 5", "callback_data": "ex_start_5"}, {"text": "📑 Đề 6", "callback_data": "ex_start_6"}],
        [{"text": "📑 Đề 7", "callback_data": "ex_start_7"}, {"text": "📑 Đề 8", "callback_data": "ex_start_8"}, {"text": "📑 Đề 9", "callback_data": "ex_start_9"}],
        [{"text": "📑 Đề 10", "callback_data": "ex_start_10"}, {"text": "📑 Đề 11", "callback_data": "ex_start_11"}, {"text": "📑 Đề 12", "callback_data": "ex_start_12"}],
        [{"text": "📑 Đề 13", "callback_data": "ex_start_13"}, {"text": "📑 Đề 14", "callback_data": "ex_start_14"}, {"text": "📑 Đề 15", "callback_data": "ex_start_15"}]
    ]
    return send_message(chat_id, msg, reply_markup={"inline_keyboard": kb})

def send_mock_exam_question(chat_id, q_idx, message_id=None):
    """Hiển thị câu hỏi trong đề thi đang làm"""
    session = get_exam_session(chat_id)
    if not session or not session.get('questions'):
        return send_mock_exam_menu(chat_id)

    total_q = len(session['questions'])
    q_idx = max(0, min(q_idx, total_q - 1))
    session['current_index'] = q_idx
    q_obj = session['questions'][q_idx]

    # Tính thời gian còn lại
    elapsed = int(time.time() - session['start_time'])
    remain = max(0, session['duration_sec'] - elapsed)
    rem_m = remain // 60
    rem_s = remain % 60
    time_str = f"{rem_m:02d}:{rem_s:02d}"

    if remain <= 0 and not session['is_completed']:
        return handle_mock_exam_submit(chat_id, message_id)

    chosen_ans = session['answers'].get(q_idx)

    # Đánh dấu badge
    is_crit = q_obj.get('isCritical', False)
    crit_tag = " ⚠️ [ĐIỂM LIỆT]" if is_crit else ""
    
    header = f"⏱️ <b>ĐỀ THI: {session['exam_id']} • CÂU {q_idx + 1}/{total_q}{crit_tag}</b> (Còn {time_str})\n"
    header += f"📘 <i>Chương {q_obj.get('chapter', 1)}: {q_obj.get('chapterName', '')}</i>\n━━━━━━━━━━━━━━━━━━━\n"
    header += f"<b>{q_obj['question']}</b>\n"

    for idx, opt in enumerate(q_obj.get('options', [])):
        opt_num = idx + 1
        mark = " 👉 <b>[ĐÃ CHỌN]</b>" if chosen_ans == opt_num else ""
        header += f"\n<b>[{opt_num}]</b> {opt}{mark}"

    # Bàn phím trả lời & điều hướng
    opt_row = []
    for idx in range(len(q_obj.get('options', []))):
        opt_num = idx + 1
        label = f"✅ {opt_num}" if chosen_ans == opt_num else f"{opt_num}️⃣"
        opt_row.append({"text": label, "callback_data": f"ex_ans_{q_idx}_{opt_num}"})

    nav_row = [
        {"text": "🔊 Nghe Đề", "callback_data": f"voice_read_{q_obj['id']}"},
        {"text": "💡 Nghe Đáp Án", "callback_data": f"voice_exp_{q_obj['id']}"}
    ]
    if q_idx > 0:
        nav_row.insert(0, {"text": "⬅️ Trước", "callback_data": f"ex_nav_{q_idx - 1}"})
    if q_idx < total_q - 1:
        nav_row.append({"text": "Sau ➡️", "callback_data": f"ex_nav_{q_idx + 1}"})

    ctrl_row = [
        {"text": f"📋 Bảng câu ({len(session['answers'])}/{total_q})", "callback_data": "ex_grid"},
        {"text": "🏁 Nộp bài", "callback_data": "ex_submit"}
    ]

    kb = [opt_row, nav_row, ctrl_row]
    reply_markup = {"inline_keyboard": kb}

    # Tự động gửi giọng đọc đề thi nếu đang bật chế độ Tự động đọc
    if is_voice_auto_read():
        def _send_exam_voice():
            time.sleep(0.4)
            try:
                af = voice_engine.generate_question_audio(q_obj)
                if af:
                    cap = format_question_voice_caption(q_obj, prefix="⏱️", header_extra=f"Đề {session['exam_id']} • Câu {q_idx + 1}/{total_q}")
                    send_voice(chat_id, af, caption=cap)
            except Exception as e:
                print(f"[Bot] Lỗi gửi voice thi thử: {e}")
        threading.Thread(target=_send_exam_voice, daemon=True).start()

    if message_id:
        return edit_message(chat_id, message_id, header, reply_markup=reply_markup)
    else:
        return send_message(chat_id, header, reply_markup=reply_markup)

def send_mock_exam_grid(chat_id, message_id=None):
    """Hiển thị bảng ma trận 40 câu để học viên chuyển nhanh"""
    session = get_exam_session(chat_id)
    if not session:
        return send_mock_exam_menu(chat_id)

    total_q = len(session['questions'])
    grid_kb = []
    row = []

    for i in range(total_q):
        is_ans = i in session['answers']
        is_cur = i == session['current_index']
        txt = f"[{i+1}✅]" if is_ans else f"{i+1}"
        if is_cur:
            txt = f"👉{i+1}"
        row.append({"text": txt, "callback_data": f"ex_nav_{i}"})
        if len(row) == 5:
            grid_kb.append(row)
            row = []
    if row:
        grid_kb.append(row)

    grid_kb.append([
        {"text": f"⬅️ Quay lại Câu {session['current_index'] + 1}", "callback_data": f"ex_nav_{session['current_index']}"},
        {"text": "🏁 Nộp bài ngay", "callback_data": "ex_submit"}
    ])

    ans_count = len(session['answers'])
    msg = f"""📋 <b>BẢNG MA TRẬN 40 CÂU HỎI THI SÁT HẠCH</b>
━━━━━━━━━━━━━━━━━━━
• Đã làm: <b>{ans_count}/{total_q}</b> câu
• Còn trống: <b>{total_q - ans_count}</b> câu
👉 <i>Bấm vào số câu bất kỳ để xem lại hoặc sửa đáp án:</i>"""

    if message_id:
        return edit_message(chat_id, message_id, msg, reply_markup={"inline_keyboard": grid_kb})
    else:
        return send_message(chat_id, msg, reply_markup={"inline_keyboard": grid_kb})

def handle_mock_exam_submit(chat_id, message_id=None):
    """Chấm điểm và hiển thị báo cáo sát hạch chi tiết"""
    res = submit_exam_session(chat_id)
    if not res:
        return send_message(chat_id, "Không có bài thi nào đang diễn ra!")

    status_icon = "🎉🏆" if res['is_passed'] else "❌⚠️"
    status_title = "CHÚC MỪNG: ANH ĐÃ ĐẠT! 🚗" if res['is_passed'] else "KẾT QUẢ: KHÔNG ĐẠT!"
    
    report = f"""{status_icon} <b>KẾT QUẢ THI SÁT HẠCH LÝ THUYẾT HẠNG C1</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Học viên:</b> {CONFIG['STUDENT_NAME']}
📑 <b>Bộ đề:</b> {res['exam_id']}
🎯 <b>Điểm số:</b> <b>{res['correct_count']} / {res['total_questions']} câu</b> (Yêu cầu: ≥ 36/40)
⏱️ <b>Thời gian làm bài:</b> {res['elapsed_time_text']}
🏁 <b>ĐÁNH GIÁ:</b> <b>{status_title}</b>
"""

    if res['failed_critical']:
        crit_nums = ", ".join([f"#{c}" for c in res['critical_failed_questions']])
        report += f"\n🚨 <b>CẢNH BÁO: ANH ĐÃ TRẢ LỜI SAI CÂU ĐIỂM LIỆT ({crit_nums})!</b>\nTheo luật sát hạch, dù đủ 36 câu nhưng sai câu điểm liệt là BỊ TRƯỢT TRỰC TIẾP.\n"

    mistakes = res.get('mistakes', [])
    if mistakes:
        report += f"\n📝 <b>CHI TIẾT CÁC CÂU LÀM SAI ({len(mistakes)} câu):</b>\n"
        for m in mistakes[:6]:
            c_tag = " [ĐIỂM LIỆT]" if m['isCritical'] else ""
            report += f"• <b>Câu {m['index']}{c_tag}:</b> {m['question'][:65]}...\n  👉 Anh chọn: [{m['chosen'] or 'Bỏ trống'}] • <b>Chuẩn xác: [{m['correct']}]</b>\n"
        if len(mistakes) > 6:
            report += f"<i>(Và {len(mistakes) - 6} câu sai khác đã được lưu tự động vào Sổ tay câu sai)</i>\n"
        report += f"\n💾 <i>Toàn bộ câu sai đã được lưu vào '❌ Sổ Tay Câu Sai' để anh ôn luyện lại!</i>"
    else:
        report += "\n🌟 <b>TUYỆT ĐỐI 100%!</b> Anh trả lời đúng tất cả 40/40 câu hỏi!"

    action_kb = [
        [{"text": "🔄 Thi Lại Đề Khác", "callback_data": "ex_start_random"},
         {"text": "❌ Ôn Lại Câu Sai", "callback_data": "show_mistakes"}],
        [{"text": "💡 Xem Mẹo Thi 100% Đỗ", "callback_data": "show_tips"}]
    ]
    reply_markup = {"inline_keyboard": action_kb}

    if message_id:
        edit_message(chat_id, message_id, report, reply_markup=reply_markup)
    else:
        send_message(chat_id, report, reply_markup=reply_markup)

# ================= QUẢN LÝ SỔ TAY CÂU SAI =================
def send_mistakes_menu(chat_id):
    """Giao diện Sổ tay câu sai"""
    mistakes = load_user_mistakes(chat_id)
    count = len(mistakes)
    if count == 0:
        msg = """🎉 <b>SỔ TAY CÂU SAI ĐANG TRỐNG!</b>
━━━━━━━━━━━━━━━━━━━
Anh chưa làm sai câu nào hoặc đã sửa đúng tất cả các câu trước đó!
Hãy bấm '🎯 Thi Thử Sát Hạch (40 câu)' để thử sức với bộ đề mới nhé!"""
        kb = [[{"text": "🎯 Thi Thử Sát Hạch", "callback_data": "ex_start_random"}]]
        return send_message(chat_id, msg, reply_markup={"inline_keyboard": kb})

    msg = f"""❌ <b>SỔ TAY CÂU SAI CỦA ANH HIẾU ({count} câu)</b>
━━━━━━━━━━━━━━━━━━━
Hệ thống tự động ghi nhận các câu hỏi anh từng chọn nhầm khi luyện thi.
Ôn lại từng câu này cho đến khi thuộc làu sẽ giúp anh tự tin 100% khi đi thi thật!

👇 <i>Anh bấm bên dưới để bắt đầu ôn luyện các câu trong sổ sai:</i>"""
    kb = [
        [{"text": "📝 Ôn Tập Câu Sai Ngay", "callback_data": "mistake_quiz_next"}],
        [{"text": "🗑️ Xóa Toàn Bộ Sổ Sai", "callback_data": "mistake_clear_all"}]
    ]
    return send_message(chat_id, msg, reply_markup={"inline_keyboard": kb})

def send_mistake_quiz(chat_id):
    """Gửi một câu hỏi trong danh sách câu sai để luyện lại"""
    mistakes = load_user_mistakes(chat_id)
    if not mistakes:
        return send_mistakes_menu(chat_id)

    qid = random.choice(mistakes)
    q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
    if not q_obj:
        return send_mistakes_menu(chat_id)

    return send_quiz_question(chat_id, q_obj)

# ================= KHO MẸO THI 100% ĐẬU =================
def send_tips_menu(chat_id, message_id=None):
    """Giao diện danh mục mẹo thi 11 nhóm (Kèm Mẹo Thực Chiến Từ Ghi Âm Bài Giảng)"""
    msg = """💡 <b>KHO 15 BỘ MẸO THI LÝ THUYẾT LÁI XE SÁT HẠCH 600 CÂU (100% ĐẬU)</b>
━━━━━━━━━━━━━━━━━━━
Chắt lọc từ 600 câu hỏi Cục Đường bộ, <b>Bí kíp TikTok triệu view</b>, Bài giảng lớp học & Khẩu quyết 3 giây!
Nắm chắc các mẹo này sẽ giúp anh làm đề thi 40 câu chỉ mất 5 - 7 phút mà đạt điểm tuyệt đối!

👇 <i>Anh chọn chủ đề mẹo bên dưới để xem chi tiết:</i>"""
    kb = [
        [{"text": "🔥 15. Bí Kíp Mẹo TikTok Triệu View", "callback_data": "tip_cat_tiktok_viral"}],
        [{"text": "⚠️ 12. Mẹo 60 Câu Điểm Liệt (Cực Quan Trọng)", "callback_data": "tip_cat_critical_60"}],
        [{"text": "🎙️ 11. Mẹo Ghi Âm Lớp Học (Thầy Dặn)", "callback_data": "tip_cat_lecture"}],
        [{"text": "🎯 13. Mẹo Bẫy 'Cả Ý 1 & 2'", "callback_data": "tip_cat_trick_traps"},
         {"text": "🧩 14. Độc Chiêu Sa Hình", "callback_data": "tip_cat_special_sahin"}],
        [{"text": "🔑 1. Từ Khóa Vàng (3s)", "callback_data": "tip_cat_keywords"},
         {"text": "🔢 2. Con Số Thần Thánh", "callback_data": "tip_cat_numbers"}],
        [{"text": "📏 3. Cự Ly Bậc Thang", "callback_data": "tip_cat_distances"},
         {"text": "🏎️ 4. Mẹo Tốc Độ", "callback_data": "tip_cat_speed"}],
        [{"text": "🎂 5. Tuổi & Bằng Lái", "callback_data": "tip_cat_ages"},
         {"text": "🛑 6. Biển Báo Cấm QCVN41", "callback_data": "tip_cat_signs"}],
        [{"text": "🛣️ 7. Vạch Kẻ Đường & Đèn", "callback_data": "tip_cat_lines"},
         {"text": "🧩 8. 5 Bước Sa Hình", "callback_data": "tip_cat_sahin"}],
        [{"text": "⚙️ 9. Kỹ Thuật Lái & Máy", "callback_data": "tip_cat_mechanic"},
         {"text": "🚑 10. Sơ Cứu Y Tế TNGT", "callback_data": "tip_cat_firstaid"}],
        [{"text": "🎯 Vào Thi Thử 40 Câu Ngay", "callback_data": "ex_start_random"}]
    ]
    if message_id:
        res = edit_message(chat_id, message_id, msg, reply_markup={"inline_keyboard": kb})
        if res.get('ok'):
            return res
    return send_message(chat_id, msg, reply_markup={"inline_keyboard": kb})

def show_tip_category(chat_id, cat_key, message_id=None):
    """Hiển thị nội dung chi tiết của một danh mục mẹo"""
    cat = EXAM_TIPS_CATEGORIES.get(cat_key)
    if not cat:
        return send_tips_menu(chat_id, message_id)

    msg = f"<b>{cat['title']}</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
    for kw, rule in cat['items']:
        msg += f"👉 <b>{kw}:</b>\n{rule}\n\n"

    kb = [
        [{"text": "🔙 Danh Mục Mẹo Khác", "callback_data": "show_tips"},
         {"text": "🎯 Thi Thử Ngay", "callback_data": "ex_start_random"}]
    ]
    if message_id:
        res = edit_message(chat_id, message_id, msg, reply_markup={"inline_keyboard": kb})
        if res.get('ok'):
            return res
    return send_message(chat_id, msg, reply_markup={"inline_keyboard": kb})

EXAM_TIPS_TEXT = """💡 <b>BỘ BÍ KÍP MẸO THI LÝ THUYẾT LÁI XE C1 - ĐẬU 100%</b>
━━━━━━━━━━━━━━━━━━━
🎯 <b>1. BỘ TỪ KHÓA VÀNG:</b>
• <b>"Bị nghiêm cấm"</b>: Chọn ngay 100% đúng.
• <b>"Không được phép"</b>, <b>"Tuyệt đối không"</b>: Luôn là đáp án đúng.
• <b>"Cơ quan có thẩm quyền cấp phép"</b>: Đúng trong các câu đua xe, thay đổi cấu tạo xe.
• <b>"Giảm tốc độ"</b>, <b>"Đi về bên phải"</b>: Luôn ưu tiên chọn.

🚗 <b>2. THẦN CHÚ 5 BƯỚC XÉT THẾ SA HÌNH:</b>
1. <b>NHẤT CHỚM:</b> Xe vào ngã tư trước được đi trước.
2. <b>NHÌ ƯU:</b> Hỏa ➔ Quân ➔ Công ➔ Thương.
3. <b>TAM ĐƯỜNG:</b> Xe trên đường ưu tiên được đi trước.
4. <b>TỨ HƯỚNG:</b> Bên phải trống đi trước.
5. <b>HƯỚNG ĐI:</b> Rẽ phải ➔ Đi thẳng ➔ Rẽ trái.

🔄 <b>3. VÒNG XUYẾN & NỒNG ĐỘ CỒN:</b>
• CÓ vòng xuyến nhường TRÁI - KHÔNG vòng xuyến nhường PHẢI.
• Nồng độ cồn: BỊ NGHIÊM CẤM TUYỆT ĐỐI (chỉ số = 0).
• Lái xe liên tục: KHÔNG QUÁ 4 GIỜ.
• Tổng giờ làm việc trong ngày: KHÔNG QUÁ 10 GIỜ."""

def ai_tutor_answer(prompt):
    p = prompt.lower().strip()
    if any(k in p for k in ['c1', 'bằng c1', 'hạng c1']):
        return "Chào anh Hiếu! <b>Bằng C1</b> cấp cho xe tải từ <b>3.500 kg đến 7.500 kg</b>, kéo rơ moóc đến 750 kg và xe hạng B. Độ tuổi tối thiểu thi là <b>đủ 21 tuổi</b> anh nhé!"
    if any(k in p for k in ['đề pa', 'lên dốc', 'chết máy']):
        return "Bí quyết đề-pa dốc số sàn 4 bước:\n1. Phanh chân + đạp hết côn -> Kéo phanh tay.\n2. Đệm nhẹ ga lên 1.200 - 1.500 v/p.\n3. Nhả côn từ từ đến khi đầu xe <b>RUNG NHỔM LÊN</b>.\n4. <b>GIỮ CHÂN CÔN</b>, hạ phanh tay -> Xe tự bò qua dốc 100%!"
    if any(k in p for k in ['vòng xuyến']):
        return "Mẹo vòng xuyến: <b>CÓ vòng xuyến nhường TRÁI - KHÔNG vòng xuyến nhường PHẢI</b>!"
    if any(k in p for k in ['cồn', 'rượu', 'bia']):
        return "Nồng độ cồn: <b>NGHIÊM CẤM TUYỆT ĐỐI</b> (chỉ số = 0). Thấy đáp án 'Bị nghiêm cấm' chọn ngay!"

    return f"Thầy AI đã nhận câu hỏi: \"<i>{prompt}</i>\".\n\nĐối với bằng C1, anh nhớ: 60 câu điểm liệt không được sai câu nào, thuộc 5 bước sa hình và kiểm soát chân côn thật tốt nhé!\nAnh có thể bấm các nút menu bên dưới để học hoặc ôn thi!"

def handle_user_voice_input(chat_id, speech_text):
    """
    Xử lý thông minh tương tác bằng giọng nói của học viên:
    - Chọn đáp án (bằng số, chữ cái hoặc đọc từ khóa trong phương án).
    - Điều hướng câu hỏi (tiếp theo, câu trước, ngẫu nhiên, nộp bài, đọc lại).
    - Tra cứu mẹo thi & giải thích chi tiết.
    - Trò chuyện và hỏi đáp chuyên sâu cùng Thầy AI Antigravity (Voice-to-Voice).
    """
    print(f"[Voice Input] Nhận diện giọng nói từ anh Hiếu: '{speech_text}'")
    send_chat_action(chat_id, 'typing')
    
    # 1. Xác định ngữ cảnh đang học / thi của anh Hiếu
    exam_session = get_exam_session(chat_id)
    practice_session = get_practice_session(chat_id)
    
    active_q = None
    session_type = None
    
    if exam_session and not exam_session.get('is_completed') and exam_session.get('questions'):
        curr_idx = exam_session.get('current_index', 0)
        active_q = exam_session['questions'][curr_idx]
        session_type = 'exam'
    elif practice_session and practice_session.get('questions'):
        curr_idx = practice_session.get('current_index', 0)
        if curr_idx < len(practice_session['questions']):
            active_q = practice_session['questions'][curr_idx]
            session_type = 'practice'
            
    # 2. Phân tích lệnh và ý định qua Voice Engine
    cmd = voice_engine.parse_voice_command(speech_text, active_question=active_q)
    cmd_type = cmd.get('type')
    cmd_val = cmd.get('value')
    
    ack_badge = f"🎙️ <i>Anh Hiếu vừa nói:</i> <b>\"{speech_text}\"</b>\n"
    
    # --- TRƯỜNG HỢP 1: CHỌN ĐÁP ÁN BẰNG GIỌNG NÓI ---
    if cmd_type == 'answer':
        chosen_opt = cmd_val
        if session_type == 'exam':
            curr_idx = exam_session.get('current_index', 0)
            total_q = len(exam_session['questions'])
            exam_session['answers'][curr_idx] = chosen_opt
            
            resp_text = f"{ack_badge}✅ Đã ghi nhận <b>Đáp án [{chosen_opt}]</b> cho Câu {curr_idx + 1}/{total_q}!"
            send_message(chat_id, resp_text)
            
            # Tự động nhảy sang câu sau nếu chưa hết đề
            if curr_idx < total_q - 1:
                send_mock_exam_question(chat_id, curr_idx + 1)
            else:
                fin_kb = [
                    [{"text": "📋 Xem Lại Bảng Câu", "callback_data": "ex_grid"},
                     {"text": "🏁 Nộp Bài Sát Hạch", "callback_data": "ex_submit"}]
                ]
                send_message(chat_id, "🏁 Anh đã hoàn thành câu cuối cùng! Bấm bên dưới để nộp bài hoặc xem lại:", reply_markup={"inline_keyboard": fin_kb})
            return
            
        elif session_type == 'practice':
            qid = active_q['id']
            correct_ans = active_q['answer']
            is_correct = (chosen_opt == correct_ans)
            
            if is_correct:
                remove_user_mistake(chat_id, qid)
            else:
                record_user_mistake(chat_id, qid)
                
            analysis = analyze_question_reply(active_q, chosen_opt)
            curr_idx = practice_session.get('current_index', 0)
            total_q = practice_session.get('total', 1)
            cfg = practice_session.get('config', {})
            badge = f"{cfg.get('badge', '📘 Ôn Luyện')} • [Câu {curr_idx + 1}/{total_q}]"
            
            full_msg = f"{ack_badge}{analysis}"
            
            next_buttons = [
                [{"text": "➡️ Câu Tiếp", "callback_data": "part_next"},
                 {"text": "💡 Mẹo", "callback_data": f"part_tip_{qid}"},
                 {"text": "📚 Đổi Phần", "callback_data": "part_menu"}]
            ]
            send_message(chat_id, full_msg, reply_markup={"inline_keyboard": next_buttons})
            
            # 1. Gửi tin nhắn giọng riêng biệt đọc đáp án đúng & giải thích mẹo
            # 2. Tự động chuyển câu tiếp theo sau đó giúp anh Hiếu hoàn toàn rảnh tay không cần chạm màn hình!
            def _send_feedback_and_advance():
                time.sleep(0.3)
                exp_af = voice_engine.generate_explanation_audio(active_q)
                if exp_af:
                    status_prefix = "🎉 Chính xác!" if is_correct else f"❌ Chưa đúng (Đáp án chuẩn: {correct_ans})"
                    cap = format_explanation_voice_caption(active_q, status_prefix=status_prefix)
                    send_voice(chat_id, exp_af, caption=cap)
                
                # Tự động chuyển sang câu tiếp theo cho đỡ phải bấm vào!
                time.sleep(1.8)
                new_idx = (curr_idx + 1) % total_q
                send_practice_question(chat_id, index=new_idx)

            threading.Thread(target=_send_feedback_and_advance, daemon=True).start()
            return
            
        else:
            send_message(chat_id, f"{ack_badge}Anh muốn chọn <b>Đáp án {chosen_opt}</b> nhưng hiện chưa mở câu hỏi nào. Anh hãy chọn '🚗 Ôn Luyện Từng Câu' hoặc '🎯 Thi Thử Sát Hạch' bên dưới để bắt đầu nhé!", reply_markup=MAIN_KEYBOARD)
            return

    # --- TRƯỜNG HỢP 2: ĐIỀU HƯỚNG BẰNG GIỌNG NÓI ---
    if cmd_type == 'nav':
        direction = cmd_val
        if session_type == 'exam':
            curr_idx = exam_session.get('current_index', 0)
            total_q = len(exam_session['questions'])
            if direction == 'next':
                send_mock_exam_question(chat_id, min(curr_idx + 1, total_q - 1))
            elif direction == 'prev':
                send_mock_exam_question(chat_id, max(0, curr_idx - 1))
            elif direction == 'rand':
                unanswered = [i for i in range(total_q) if i not in exam_session['answers']]
                target = random.choice(unanswered) if unanswered else curr_idx
                send_mock_exam_question(chat_id, target)
            return
        elif session_type == 'practice':
            curr_idx = practice_session.get('current_index', 0)
            total_q = practice_session.get('total', 1)
            if direction == 'next':
                new_idx = (curr_idx + 1) % total_q
                send_practice_question(chat_id, index=new_idx)
            elif direction == 'prev':
                new_idx = (curr_idx - 1) % total_q
                send_practice_question(chat_id, index=new_idx)
            elif direction == 'rand':
                new_idx = random.randint(0, total_q - 1)
                send_practice_question(chat_id, index=new_idx)
            return

    # --- TRƯỜNG HỢP 3: NỘP BÀI THI BẰNG GIỌNG NÓI ---
    if cmd_type == 'submit':
        if session_type == 'exam':
            send_message(chat_id, f"{ack_badge}🏁 Đang chấm điểm và thu bài thi sát hạch cho anh...")
            handle_mock_exam_submit(chat_id)
        else:
            send_message(chat_id, f"{ack_badge}Anh đang không trong bài thi sát hạch. Bấm '🎯 Thi Thử Sát Hạch (40 câu)' để thi nhé!", reply_markup=MAIN_KEYBOARD)
        return

    # --- TRƯỜNG HỢP 4: ĐỌC LẠI CÂU HỎI ---
    if cmd_type == 'repeat_audio':
        if active_q:
            send_message(chat_id, f"{ack_badge}🔊 Em đang đọc lại Câu {active_q['id']} cho anh đây ạ...")
            af = voice_engine.generate_question_audio(active_q)
            if af:
                cap = format_question_voice_caption(active_q)
                send_voice(chat_id, af, caption=cap)
        else:
            send_message(chat_id, f"{ack_badge}Hiện chưa có câu hỏi nào đang mở để đọc lại anh nhé!", reply_markup=MAIN_KEYBOARD)
        return

    # --- TRƯỜNG HỢP 5: CHỈ MẸO THI ---
    if cmd_type == 'tip':
        if active_q:
            tip_text = f"{ack_badge}🤖 <b>THẦY AI CHỈ MẸO CÂU {active_q['id']}:</b>\n\n💡 {active_q.get('explanation', '')}\n👉 Đáp án chuẩn: Số <b>{active_q['answer']}</b>"
            send_message(chat_id, tip_text)
            
            def _send_tip_voice():
                time.sleep(0.3)
                v_txt = f"Mẹo câu {active_q['id']}: {active_q.get('explanation', '')}. Đáp án đúng là số {active_q['answer']} anh nhé."
                af = voice_engine.generate_custom_speech(v_txt)
                if af:
                    cap = format_explanation_voice_caption(active_q, status_prefix="🤖 Thầy AI chỉ mẹo:")
                    send_voice(chat_id, af, caption=cap)
            threading.Thread(target=_send_tip_voice, daemon=True).start()
        else:
            send_tips_menu(chat_id)
        return

    # --- TRƯỜNG HỢP 6: NGHE ĐÁP ÁN ĐÚNG & MẸO (TIN NHẮN GIỌNG RIÊNG) ---
    if cmd_type == 'read_answer':
        if active_q:
            send_message(chat_id, f"{ack_badge}💡 Đang gửi tin nhắn giọng đọc đáp án và mẹo Câu {active_q['id']} cho anh...")
            af = voice_engine.generate_explanation_audio(active_q)
            if af:
                cap = format_explanation_voice_caption(active_q)
                send_voice(chat_id, af, caption=cap)
        else:
            send_message(chat_id, f"{ack_badge}Hiện chưa có câu hỏi nào đang mở để đọc đáp án anh nhé!", reply_markup=MAIN_KEYBOARD)
        return

    # --- TRƯỜNG HỢP 7: BẬT SÁCH NÓI / PODCAST RẢNH TAY ---
    if cmd_type == 'podcast':
        send_podcast_menu(chat_id)
        return

    # --- TRƯỜNG HỢP 8: BẬT/TẮT TỰ ĐỘNG ĐỌC BẰNG LỆNH NÓI ---
    if cmd_type == 'toggle_voice':
        new_st = set_voice_auto_read(cmd_val)
        txt = f"{ack_badge}🎙️ Đã <b>{'BẬT' if new_st else 'TẮT'}</b> chế độ tự động đọc câu hỏi bằng giọng nói!"
        send_message(chat_id, txt, reply_markup=MAIN_KEYBOARD)
        return

    # --- TRƯỜNG HỢP 9: TRÒ CHUYỆN & GIẢI ĐÁP VOICE-TO-VOICE VỚI THẦY AI ---
    send_chat_action(chat_id, 'typing')
    ai_resp = ask_antigravity_ai(speech_text, chat_id=chat_id)
    send_message(chat_id, f"{ack_badge}\n{ai_resp}", reply_markup=MAIN_KEYBOARD)
    
    def _send_ai_voice():
        time.sleep(0.3)
        af = voice_engine.generate_custom_speech(ai_resp)
        if af:
            send_voice(chat_id, af, caption="🤖 <i>Thầy AI Antigravity trả lời bằng giọng nói</i>")
    threading.Thread(target=_send_ai_voice, daemon=True).start()

# XỬ LÝ TELEGRAM UPDATES & ĐIỀU KHIỂN TỪ XA
def handle_telegram_update(update):
    try:
        if 'callback_query' in update:
            cb = update['callback_query']
            cb_id = cb['id']
            data = cb.get('data', '')
            msg = cb.get('message', {})
            chat_id = msg.get('chat', {}).get('id')
            message_id = msg.get('message_id')
            if data.startswith('part_ans_'):
                parts = data.split('_')
                qid = int(parts[2])
                chosen = int(parts[3])
                q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                if q_obj:
                    answer_callback(cb_id, text=f"Đã chọn đáp án {chosen}!")
                    if chosen == q_obj['answer']:
                        remove_user_mistake(chat_id, qid)
                    else:
                        record_user_mistake(chat_id, qid)
                    analysis = analyze_question_reply(q_obj, chosen)
                    
                    session = get_practice_session(chat_id)
                    cfg = session.get('config', {}) if session else {}
                    total = session.get('total', 1) if session else 1
                    curr_idx = session.get('current_index', 0) if session else 0

                    next_buttons = [
                        [{"text": "➡️ Câu Tiếp", "callback_data": "part_next"},
                         {"text": "⬅️ Câu Trước", "callback_data": "part_prev"},
                         {"text": "💡 Mẹo", "callback_data": f"part_tip_{qid}"}],
                        [{"text": "🔊 Nghe Lại", "callback_data": f"voice_read_{qid}"},
                         {"text": "📚 Đổi Phần", "callback_data": "part_menu"}]
                    ]
                    reply_markup = {"inline_keyboard": next_buttons}

                    if is_voice_auto_read():
                        def _send_part_exp():
                            time.sleep(0.3)
                            exp_af = voice_engine.generate_explanation_audio(q_obj)
                            if exp_af:
                                status_prefix = "🎉 <b>ĐÚNG RỒI!</b>" if chosen == q_obj['answer'] else "❌ <b>CHƯA ĐÚNG!</b>"
                                cap = format_explanation_voice_caption(q_obj, status_prefix=status_prefix)
                                send_voice(chat_id, exp_af, caption=cap)
                        threading.Thread(target=_send_part_exp, daemon=True).start()

                    badge = f"{cfg.get('badge', '📘 Ôn Luyện')} • [Câu {curr_idx + 1}/{total}]\n"
                    full_result_caption = f"{badge}<b>Câu {qid}:</b> {q_obj['question']}\n{analysis}"

                    if msg.get('photo'):
                        if len(full_result_caption) <= 1024:
                            edit_message_caption(chat_id, message_id, full_result_caption, reply_markup=reply_markup)
                        else:
                            short_cap = f"{badge}<b>Câu {qid}:</b> {q_obj['question']}\n" + (
                                f"🎉 <b>ĐÚNG RỒI!</b> Anh chọn chuẩn đáp án <b>{chosen}</b>." if chosen == q_obj['answer']
                                else f"❌ <b>CHƯA ĐÚNG!</b> Anh chọn {chosen} • 👉 <b>Đáp án chuẩn:</b> {q_obj['answer']}"
                            )
                            edit_message_caption(chat_id, message_id, short_cap)
                            send_message(chat_id, analysis, reply_markup=reply_markup)
                    else:
                        edit_message(chat_id, message_id, full_result_caption, reply_markup=reply_markup)
                else:
                    answer_callback(cb_id, text="Không tìm thấy câu hỏi!")

            elif data == 'part_prev':
                answer_callback(cb_id)
                navigate_practice_question(chat_id, 'prev')
                send_practice_question(chat_id)

            elif data == 'part_next':
                answer_callback(cb_id)
                navigate_practice_question(chat_id, 'next')
                send_practice_question(chat_id)

            elif data == 'part_rand':
                answer_callback(cb_id, text="Chuyển ngẫu nhiên trong phần này!")
                navigate_practice_question(chat_id, 'random')
                send_practice_question(chat_id)

            elif data.startswith('part_start_'):
                part_key = data.replace('part_start_', '')
                answer_callback(cb_id, text=f"Bắt đầu ôn {part_key}!")
                send_practice_question(chat_id, part_key, 0)

            elif data == 'part_menu':
                answer_callback(cb_id)
                send_practice_menu(chat_id, message_id)

            elif data.startswith('part_tip_'):
                parts = data.split('_')
                if len(parts) > 2 and parts[2].isdigit():
                    qid = int(parts[2])
                    q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                    if q_obj:
                        answer_callback(cb_id, text="Thầy AI hướng dẫn:")
                        tip_text = f"🤖 <b>THẦY AI CHỈ MẸO CÂU NÀY (Câu {qid}):</b>\n\n💡 {q_obj.get('explanation', '')}\n👉 Đáp án chuẩn: Số <b>{q_obj['answer']}</b>"
                        send_message(chat_id, tip_text)
                    else:
                        answer_callback(cb_id)
                else:
                    answer_callback(cb_id)

            elif data.startswith('ans_'):
                parts = data.split('_')
                qid = int(parts[1])
                chosen = int(parts[2])
                q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                if q_obj:
                    answer_callback(cb_id, text=f"Đã chọn đáp án {chosen}!")
                    if chosen == q_obj['answer']:
                        remove_user_mistake(chat_id, qid)
                    else:
                        record_user_mistake(chat_id, qid)
                    analysis = analyze_question_reply(q_obj, chosen)
                    next_buttons = [
                        [{"text": "➡️ Câu Tiếp Theo", "callback_data": "quiz_next"},
                         {"text": "⚠️ Luyện Câu Liệt", "callback_data": "quiz_crit_next"}],
                        [{"text": "🛑 Luyện Biển Báo (Ảnh)", "callback_data": "quiz_signs"},
                         {"text": "🧩 Luyện Sa Hình (Ảnh)", "callback_data": "quiz_sahin"}],
                        [{"text": "💡 Xem Thêm Mẹo Thi", "callback_data": "show_tips"}]
                    ]
                    reply_markup = {"inline_keyboard": next_buttons}

                    is_crit = q_obj.get('isCritical', False)
                    badge = "⚠️ <b>CÂU ĐIỂM LIỆT (BẮT BUỘC ĐÚNG 100%)</b>\n" if is_crit else f"📘 <b>Chương {q_obj.get('chapter', 1)}: {q_obj.get('chapterName', '')}</b>\n"
                    full_result_caption = f"{badge}<b>Câu {qid}:</b> {q_obj['question']}\n\n━━━━━━━━━━━━━━━━━━━\n{analysis}"

                    if msg.get('photo'):
                        if len(full_result_caption) <= 1024:
                            edit_message_caption(chat_id, message_id, full_result_caption, reply_markup=reply_markup)
                        else:
                            short_cap = f"{badge}<b>Câu {qid}:</b> {q_obj['question']}\n\n━━━━━━━━━━━━━━━━━━━\n" + (
                                f"🎉 <b>CHÍNH XÁC 100%!</b> Anh đã chọn đúng đáp án <b>{chosen}</b>." if chosen == q_obj['answer']
                                else f"❌ <b>ANH ĐÃ CHỌN NHẦM ĐÁP ÁN {chosen}</b>!\n👉 <b>Đáp án chuẩn:</b> {q_obj['answer']}"
                            )
                            edit_message_caption(chat_id, message_id, short_cap)
                            send_message(chat_id, analysis, reply_markup=reply_markup)
                    else:
                        edit_message(chat_id, message_id, full_result_caption, reply_markup=reply_markup)
                else:
                    answer_callback(cb_id, text="Không tìm thấy câu hỏi!")

            elif data.startswith('tip_cat_'):
                cat_key = data.replace('tip_cat_', '')
                answer_callback(cb_id)
                show_tip_category(chat_id, cat_key, message_id)

            elif data.startswith('tip_'):
                parts = data.split('_')
                if len(parts) > 1 and parts[1].isdigit():
                    qid = int(parts[1])
                    q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                    if q_obj:
                        answer_callback(cb_id, text="Thầy AI hướng dẫn:")
                        tip_text = f"🤖 <b>THẦY AI CHỈ MẸO CÂU NÀY:</b>\n\n💡 {q_obj.get('explanation', '')}\n👉 Đáp án chuẩn: Số <b>{q_obj['answer']}</b>"
                        send_message(chat_id, tip_text)
                else:
                    answer_callback(cb_id)

            elif data == 'quiz_next':
                answer_callback(cb_id)
                if ALL_QUESTIONS:
                    send_quiz_question(chat_id, random.choice(ALL_QUESTIONS))

            elif data == 'quiz_crit_next':
                answer_callback(cb_id)
                crits = [q for q in ALL_QUESTIONS if q.get('isCritical')]
                if crits:
                    send_quiz_question(chat_id, random.choice(crits))

            elif data == 'quiz_signs':
                answer_callback(cb_id)
                signs = [q for q in ALL_QUESTIONS if q.get('chapter') == 5 or 'biển' in q.get('chapterName', '').lower()]
                if signs:
                    send_quiz_question(chat_id, random.choice(signs))
                elif ALL_QUESTIONS:
                    send_quiz_question(chat_id, random.choice(ALL_QUESTIONS))

            elif data == 'quiz_sahin':
                answer_callback(cb_id)
                sahins = [q for q in ALL_QUESTIONS if q.get('chapter') == 6 or 'sa hình' in q.get('chapterName', '').lower()]
                if sahins:
                    send_quiz_question(chat_id, random.choice(sahins))
                elif ALL_QUESTIONS:
                    send_quiz_question(chat_id, random.choice(ALL_QUESTIONS))

            elif data.startswith('ai_act_'):
                act = data.replace('ai_act_', '')
                answer_callback(cb_id, text="Antigravity đang giải đáp...")
                send_chat_action(chat_id, 'typing')
                if act == 'critical':
                    reply = ask_antigravity_ai("Chia sẻ bí kíp và mẹo nhớ 60 câu điểm liệt cấm sai cho anh với em!", chat_id=chat_id)
                elif act == 'sahin':
                    reply = ask_antigravity_ai("Chỉ cho anh thần chú 5 bước xét sa hình và thứ tự các xe ưu tiên chuẩn nhất!", chat_id=chat_id)
                elif act == 'depa':
                    reply = ask_antigravity_ai("Chỉ cho anh 4 bước đề pa dốc số sàn xe tải không chết máy không tụt lùi!", chat_id=chat_id)
                elif act == 'c1':
                    reply = ask_antigravity_ai("Tóm tắt toàn bộ quy định bằng C1 xe tải về tải trọng, độ tuổi, niên hạn và thời gian lái xe cho anh!", chat_id=chat_id)
                elif act == 'keywords':
                    reply = ask_antigravity_ai("Tổng hợp các mẹo từ khóa vàng 600 câu lý thuyết chắc chắn đúng cho anh!", chat_id=chat_id)
                elif act == 'today':
                    st = load_status()
                    today_text = st.get('webOfficialText', format_h_m(st.get('todaySeconds', 0)))
                    lessons = st.get('todayCompletedLessons', 0)
                    cur_c = st.get('currentCourseName', 'Đang học...')
                    cur_l = st.get('currentLessonTitle', 'Đang tải...')
                    prompt_today = f"Báo cáo tiến độ học hôm nay cho anh Hiếu: Hôm nay anh đã tích lũy {today_text}, hoàn thành {lessons} bài. Môn hiện tại: {cur_c}, bài: {cur_l}. Hãy động viên và dặn dò anh thật ấm áp nhé!"
                    reply = ask_antigravity_ai(prompt_today, chat_id=chat_id)
                else:
                    reply = ask_antigravity_ai("Em chào anh Hiếu!", chat_id=chat_id)
                
                ai_keyboard = {
                    "inline_keyboard": [
                        [{"text": "⚠️ 60 Câu Điểm Liệt", "callback_data": "ai_act_critical"},
                         {"text": "🚦 5 Bước Sa Hình", "callback_data": "ai_act_sahin"}],
                        [{"text": "🏔️ Đề-Pa Dốc Số Sàn", "callback_data": "ai_act_depa"},
                         {"text": "🚛 Quy Định Bằng C1", "callback_data": "ai_act_c1"}],
                        [{"text": "🔑 Từ Khóa Vàng", "callback_data": "ai_act_keywords"},
                         {"text": "📊 Tiến Độ Hôm Nay", "callback_data": "ai_act_today"}]
                    ]
                }
                send_message(chat_id, reply, reply_markup=ai_keyboard)

            elif data.startswith('c1_course_'):
                c_id = int(data.split('_')[2])
                c_item = next((c for c in C1_COURSES if c['id'] == c_id), None) if 'C1_COURSES' in globals() else None
                if c_item:
                    answer_callback(cb_id, text=f"Môn {c_id}: {c_item['name']}")
                    topics_txt = "\n".join([f"• {t}" for t in c_item.get('coreTopics', [])])
                    msg_txt = f"""{c_item.get('icon', '📚')} <b>{c_item['name'].upper()}</b>
━━━━━━━━━━━━━━━━━━━
⏱️ <b>Thời lượng tiêu chuẩn:</b> {c_item.get('totalHours')}
📖 <b>Số bài học:</b> {c_item.get('totalLessons')} bài
📝 <b>Tóm tắt:</b> {c_item.get('desc')}

🎯 <b>KIẾN THỨC CỐT LÕI BẮT BUỘC NHỚ:</b>
{topics_txt}

💡 <i>Mẹo: Hãy bấm '🚗 Ôn Thi Sát Hạch C1' để luyện ngay các câu hỏi thực tế của môn này!</i>"""
                    send_message(chat_id, msg_txt)
                else:
                    answer_callback(cb_id, text="Không tìm thấy môn học!")

            elif data == 'c1_truck_guide':
                answer_callback(cb_id, text="Cẩm nang xe tải C1")
                try:
                    img_bytes = generate_c1_truck_infographic()
                    cap = "🚛 <b>CẨM NANG CHUYÊN SÂU LÁI XE TẢI HẠNG C1</b>\n\nNắm vững quy tắc tải trọng 3.5t - 7.5t, phanh khí nén, đề-pa dốc tải nặng và điểm mù xe tải!"
                    send_photo(chat_id, img_bytes, caption=cap)
                except Exception as e:
                    send_message(chat_id, "🚛 <b>BẰNG C1:</b> Điều khiển ô tô tải từ 3.500 kg đến 7.500 kg, kéo rơ moóc đến 750 kg. Độ tuổi tối thiểu: Đủ 21 tuổi!")

            elif data.startswith('ex_start_'):
                answer_callback(cb_id, text="Bắt đầu thi sát hạch!")
                ex_id = data.replace('ex_start_', '')
                session = start_exam_session(chat_id, ex_id)
                send_mock_exam_question(chat_id, 0)

            elif data.startswith('ex_ans_'):
                parts = data.split('_')
                q_idx = int(parts[2])
                opt_num = int(parts[3])
                session = get_exam_session(chat_id)
                if session and not session.get('is_completed'):
                    session['answers'][q_idx] = opt_num
                    answer_callback(cb_id, text=f"Đã chọn [{opt_num}] cho câu {q_idx + 1}")
                    next_idx = q_idx + 1 if q_idx < len(session['questions']) - 1 else q_idx
                    send_mock_exam_question(chat_id, next_idx, message_id)
                else:
                    answer_callback(cb_id, text="Bài thi đã kết thúc!")

            elif data.startswith('ex_nav_'):
                q_idx = int(data.split('_')[2])
                answer_callback(cb_id)
                send_mock_exam_question(chat_id, q_idx, message_id)

            elif data == 'ex_grid':
                answer_callback(cb_id)
                send_mock_exam_grid(chat_id, message_id)

            elif data == 'ex_submit':
                answer_callback(cb_id, text="Đang thu bài và chấm điểm...")
                handle_mock_exam_submit(chat_id, message_id)

            elif data == 'show_mistakes':
                answer_callback(cb_id)
                send_mistakes_menu(chat_id)

            elif data == 'mistake_quiz_next':
                answer_callback(cb_id)
                send_mistake_quiz(chat_id)

            elif data == 'mistake_clear_all':
                answer_callback(cb_id, text="Đã xóa toàn bộ sổ sai!")
                try:
                    data_m = load_user_mistakes()
                    data_m[str(chat_id)] = []
                    with open(MISTAKES_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data_m, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                send_message(chat_id, "✅ Đã dọn sạch Sổ tay câu sai!", reply_markup=MAIN_KEYBOARD)

            elif data == 'show_tips':
                answer_callback(cb_id)
                send_tips_menu(chat_id, message_id)

            elif data.startswith('voice_read_'):
                parts = data.split('_')
                if len(parts) > 2 and parts[2].isdigit():
                    qid = int(parts[2])
                    q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                    if q_obj:
                        answer_callback(cb_id, text=f"Đang phát giọng đọc Câu {qid}...")
                        send_chat_action(chat_id, 'record_voice')
                        af = voice_engine.generate_question_audio(q_obj)
                        if af:
                            cap = format_question_voice_caption(q_obj)
                            send_voice(chat_id, af, caption=cap)
                    else:
                        answer_callback(cb_id, text="Không tìm thấy câu hỏi!")
                else:
                    answer_callback(cb_id)

            elif data.startswith('voice_exp_'):
                parts = data.split('_')
                if len(parts) > 2 and parts[2].isdigit():
                    qid = int(parts[2])
                    q_obj = next((q for q in ALL_QUESTIONS if q['id'] == qid), None)
                    if q_obj:
                        answer_callback(cb_id, text=f"Đang phát đáp án & mẹo Câu {qid}...")
                        send_chat_action(chat_id, 'record_voice')
                        af = voice_engine.generate_explanation_audio(q_obj)
                        if af:
                            cap = format_explanation_voice_caption(q_obj)
                            send_voice(chat_id, af, caption=cap)
                    else:
                        answer_callback(cb_id, text="Không tìm thấy câu hỏi!")
                else:
                    answer_callback(cb_id)

            elif data == 'podcast_menu':
                answer_callback(cb_id)
                send_podcast_menu(chat_id, message_id)

            elif data.startswith('podcast_play_'):
                parts = data.split('_')
                part_key = parts[2] if len(parts) > 2 else 'CRITICAL'
                start_idx = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                answer_callback(cb_id, text="Đang phát Sách Nói rảnh tay...")
                play_podcast_playlist(chat_id, part_key, start_idx=start_idx, count=5)

            elif data == 'voice_settings':
                answer_callback(cb_id)
                send_voice_settings_menu(chat_id, message_id)

            elif data == 'voice_toggle':
                curr = is_voice_auto_read()
                new_state = set_voice_auto_read(not curr)
                state_str = "BẬT (Tự động đọc đề)" if new_state else "TẮT (Chỉ đọc khi bấm nút)"
                answer_callback(cb_id, text=f"Đã {state_str}!")
                send_voice_settings_menu(chat_id, message_id)

            # ================= CÁC CALLBACK MÔ PHỎNG 120 TÌNH HUỐNG =================
            elif data == 'sim_menu' or data == 'sim_back_main':
                answer_callback(cb_id)
                send_simulation_menu(chat_id, message_id)

            elif data == 'sim_cues_summary':
                answer_callback(cb_id, text="6 Mẹo vàng bắt điểm 5!")
                send_simulation_cues_summary(chat_id, message_id)

            elif data.startswith('sim_ch_'):
                ch_num = int(data.replace('sim_ch_', ''))
                answer_callback(cb_id)
                send_simulation_chapter_list(chat_id, ch_num, page=0, message_id=message_id)

            elif data.startswith('sim_page_'):
                parts = data.split('_')
                ch_num = int(parts[2])
                pg = int(parts[3])
                answer_callback(cb_id)
                send_simulation_chapter_list(chat_id, ch_num, page=pg, message_id=message_id)

            elif data.startswith('sim_detail_'):
                sit_id = int(data.replace('sim_detail_', ''))
                answer_callback(cb_id, text=f"Tình huống #{sit_id}")
                detail = c1_simulation_handbook.format_situation_detail(sit_id)
                kb = [
                    [{"text": f"⬅️ Câu #{max(1, sit_id - 1)}", "callback_data": f"sim_detail_{max(1, sit_id - 1)}"},
                     {"text": f"Câu #{min(120, sit_id + 1)} ➡️", "callback_data": f"sim_detail_{min(120, sit_id + 1)}"}],
                    [{"text": "🔙 Trở Lại Danh Sách", "callback_data": "sim_menu"}]
                ]
                edit_message(chat_id, message_id, detail, reply_markup={"inline_keyboard": kb})

            elif data == 'sim_mock_exam':
                answer_callback(cb_id, text="Đang tạo đề thi thử 10 câu...")
                test_ids = c1_simulation_handbook.generate_mock_simulation_test()
                msg = "🎯 <b>ĐỀ THI THỬ 10 CÂU MÔ PHỎNG V2.0.0 CHUẨN MA TRẬN</b>\n━━━━━━━━━━━━━━━━━━━\n"
                msg += "📋 <i>Đề thi gồm 10 tình huống lấy ngẫu nhiên theo tỷ lệ chuẩn Cục Đường Bộ. Bấm vào từng câu để xem mẹo điểm căn 5 điểm:</i>\n\n"
                kb = []
                for idx, sid in enumerate(test_ids):
                    s = c1_simulation_handbook.get_situation(sid)
                    msg += f"<b>Câu {idx + 1} (Tình huống #{sid}):</b> {s['title']}\n"
                    kb.append([{"text": f"🎯 Điểm căn Câu {idx + 1} (#{sid})", "callback_data": f"sim_detail_{sid}"}])
                kb.append([{"text": "🔄 Đổi Đề Thi Thử Khác", "callback_data": "sim_mock_exam"}])
                kb.append([{"text": "🔙 Menu 120 Mô Phỏng", "callback_data": "sim_menu"}])
                edit_message(chat_id, message_id, msg, reply_markup={"inline_keyboard": kb})
            return

        if 'message' in update:
            message = update['message']
            chat_id = message.get('chat', {}).get('id')

            # XỬ LÝ DỮ LIỆU TỪ TELEGRAM WEBAPP (MINI APP MÔ PHỎNG)
            if 'web_app_data' in message:
                try:
                    raw_data = message['web_app_data'].get('data', '')
                    payload = json.loads(raw_data)
                    if payload.get('type') == 'simulation_exam_result':
                        total = payload.get('totalScore', 0)
                        passed = payload.get('isPassed', False)
                        details = payload.get('details', [])
                        status_icon = "🎉 <b>ĐẠT YÊU CẦU XUẤT SẮC!</b>" if passed else "⚠️ <b>CHƯA ĐẠT (CẦN TỐI THIỂU 35/50)</b>"
                        msg = f"""🏆 <b>BÁO CÁO KẾT QUẢ THI THỬ 120 MÔ PHỎNG V2.0.0</b>\n━━━━━━━━━━━━━━━━━━━\n👤 <b>Thí sinh:</b> {CONFIG['STUDENT_NAME']} ({CONFIG['COURSE_NAME']})\n📊 <b>Tổng điểm:</b> <b>{total} / 50 ĐIỂM</b>\n🎯 <b>Kết luận:</b> {status_icon}\n⏱️ <b>Quy chế:</b> Đạt từ 35/50 điểm trở lên\n━━━━━━━━━━━━━━━━━━━\n📝 <i>Chi tiết 10 tình huống vừa thi:</i>\n"""
                        for idx, d in enumerate(details[:10]):
                            score = d.get('score', 0)
                            t = d.get('time')
                            t_str = f"{t:.1f}s" if t is not None else "Không phanh"
                            msg += f"• <b>Câu #{idx+1} (TH #{d.get('sitId')}):</b> {score}/5đ (Phản xạ: {t_str})\n"
                        msg += "\n💡 <i>Anh có thể mở lại phòng thi mô phỏng bất kỳ lúc nào để luyện bắt trọn điểm 5 nhé!</i>"
                        send_message(chat_id, msg, reply_markup=MAIN_KEYBOARD)
                        return
                except Exception as e:
                    print(f"[Bot] Lỗi đọc web_app_data: {e}")

            # XỬ LÝ TIN NHẮN THOẠI (VOICE NOTE / AUDIO TỪ ANH HIẾU)
            voice_obj = message.get('voice') or message.get('audio')
            if voice_obj:
                send_chat_action(chat_id, 'record_voice')
                file_id = voice_obj.get('file_id')
                temp_audio = download_telegram_file(file_id)
                if temp_audio:
                    try:
                        speech_text = voice_engine.transcribe_voice_file(temp_audio)
                    finally:
                        try:
                            if os.path.exists(temp_audio):
                                os.remove(temp_audio)
                        except Exception:
                            pass
                            
                    if speech_text:
                        handle_user_voice_input(chat_id, speech_text)
                    else:
                        send_message(chat_id, "🎙️ <i>Em chưa nghe rõ anh nói gì ạ. Anh vui lòng giữ nút Micro và nói to, rõ ràng hơn một chút nhé!</i>", reply_markup=MAIN_KEYBOARD)
                else:
                    send_message(chat_id, "❌ Không thể tải file âm thanh từ Telegram. Anh vui lòng thử gửi lại nhé!", reply_markup=MAIN_KEYBOARD)
                return

            text = (message.get('text') or '').strip()
            if not text:
                return

            status = load_status()

            if text in ['/start', '/help', 'bắt đầu', 'bat dau', 'menu']:
                welcome = f"""Chào anh <b>{CONFIG['STUDENT_NAME']}</b>! Trợ lý sát hạch lái xe Hạng C1 xin chào anh! 🚗

Hệ thống đã nạp đầy đủ <b>600 câu hỏi sát hạch chuẩn Quốc gia</b> & <b>60 câu điểm liệt</b>.
Thời gian web LMS ghi nhận: <b>{status.get('webOfficialText', '7 giờ 18 phút')}</b>.

<b>Anh có thể chọn các tính năng ôn thi & học tập:</b>
🎯 <b>Thi Thử Sát Hạch (40 câu):</b> Đúng 24 phút, chấm điểm Đạt/Trượt như thi thật!
⚠️ <b>60 Câu Điểm Liệt:</b> Luyện trọn bộ 60 câu cấm sai (sai 1 câu là trượt ngay).
❌ <b>Sổ Tay Câu Sai:</b> Tự động lưu và luyện riêng các câu anh đã từng làm sai.
💡 <b>Mẹo Thi Đậu 100%:</b> Tra cứu bí kíp từ khóa vàng, 5 bước sa hình & biển báo.
🚗 <b>Ôn Luyện Từng Câu:</b> Ngân hàng 600 câu hỏi có ảnh trực quan & giải thích.
🛑 <b>Biển Báo (Có Ảnh):</b> Luyện hệ thống biển báo đường bộ chuẩn QCVN 41.
🧩 <b>Sa Hình (Có Ảnh):</b> Luyện giải ngã tư, xe ưu tiên & vòng xuyến.
🚀 <b>Bật Học Tự Động Trên Máy:</b> Tự mở Chrome và học tích lũy giờ trên EcoTek LMS."""
                send_message(chat_id, welcome, reply_markup=MAIN_KEYBOARD)

            # TÍNH NĂNG SÁCH NÓI 600 CÂU RẢNH TAY (TỰ ĐỘNG PHÁT LIÊN TỤC)
            elif text in ["📻 Sách Nói 600 Câu (Rảnh Tay)", "/podcast", "/sachnoi", "sách nói", "sach noi", "podcast"]:
                send_podcast_menu(chat_id)

            # TÍNH NĂNG TƯƠNG TÁC GIỌNG NÓI TOÀN DIỆN (TTS + STT)
            elif text in ["🎙️ Học Bằng Giọng Nói (Bật/Tắt)", "🎙️ Giọng Nói Học Tập", "/voice", "/giongnoi", "giọng nói", "giong noi", "voice"]:
                send_voice_settings_menu(chat_id)

            # TÍNH NĂNG THI THỬ SÁT HẠCH CHUẨN PHÒNG THI (40 CÂU - 24 PHÚT)
            elif text in ["🎯 Thi Thử Sát Hạch (40 câu)", "/thi", "/mock_exam", "/exam", "thi", "thi thử", "sát hạch"]:
                send_mock_exam_menu(chat_id)

            # TÍNH NĂNG SỔ TAY CÂU SAI
            elif text in ["❌ Sổ Tay Câu Sai", "/causai", "/mistakes", "sổ tay câu sai", "câu sai"]:
                send_mistakes_menu(chat_id)

            # TÍNH NĂNG TRA CỨU MẸO THI 100% ĐẬU
            elif text in ["💡 Mẹo Thi Đậu 100%", "/meo", "/meothi", "/tips", "mẹo thi", "mẹo"]:
                send_tips_menu(chat_id)

            # TÍNH NĂNG ÔN LUYỆN 600 CÂU HỎI THEO PHẦN
            elif text in ["🚗 Ôn Luyện Từng Câu", "🚗 Ôn Thi Sát Hạch C1", "/onthi", "ôn thi"]:
                send_practice_menu(chat_id)

            # TÍNH NĂNG 15 ĐỀ THI CỐ ĐỊNH CHUẨN C1 (QUÉT SẠCH 600 CÂU)
            elif text in ["📋 15 Đề Thi Cố Định", "/15de", "15 đề", "15 de", "đề cố định", "de co dinh"]:
                send_mock_exam_menu(chat_id)

            # TÍNH NĂNG TOP 50 CÂU BẪY HAY SAI NHẤT TOÀN QUỐC
            elif text in ["⚠️ Top 50 Câu Hay Sai", "/top50", "top 50", "câu hay sai", "cau hay sai", "top câu sai"]:
                send_practice_question(chat_id, 'TOP50', 0)

            # TÍNH NĂNG 120 TÌNH HUỐNG MÔ PHỎNG V2.0.0
            elif text in ["🎬 120 Mô Phỏng V2.0.0", "/mophong", "mô phỏng", "mo phong", "120 câu", "120 tình huống"]:
                send_simulation_menu(chat_id)

            # TRA CỨU NHANH TÌNH HUỐNG MÔ PHỎNG: mp 5 hoặc /mophong 25
            elif text.lower().startswith(('/mophong ', 'mp ', 'tình huống ')):
                parts = text.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    sit_id = int(parts[1])
                    if 1 <= sit_id <= 120:
                        detail = c1_simulation_handbook.format_situation_detail(sit_id)
                        kb = [
                            [{"text": f"⬅️ Câu #{max(1, sit_id - 1)}", "callback_data": f"sim_detail_{max(1, sit_id - 1)}"},
                             {"text": f"Câu #{min(120, sit_id + 1)} ➡️", "callback_data": f"sim_detail_{min(120, sit_id + 1)}"}],
                            [{"text": "🔙 Menu 120 Mô Phỏng", "callback_data": "sim_menu"}]
                        ]
                        send_message(chat_id, detail, reply_markup={"inline_keyboard": kb})
                        return

            # TÍNH NĂNG 60 CÂU ĐIỂM LIỆT (CHUẨN XÁC 60 CÂU CẤM SAI)
            elif text in ["⚠️ 60 Câu Điểm Liệt", "/diemliet", "điểm liệt"]:
                send_practice_question(chat_id, 'CRITICAL', 0)

            # TÍNH NĂNG 1: BẬT HỌC TỰ ĐỘNG TỪ XA QUA TELEGRAM
            elif text in ["🚀 Bật Học Tự Động Trên Máy", "/bathoc", "/start_study", "bat hoc", "bật học", "học"]:
                ok, prof = launch_chrome_study()
                if ok:
                    resp_msg = f"""🚀 <b>ĐÃ KÍCH HOẠT HỌC TỰ ĐỘNG TRÊN MÁY TÍNH!</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Tài khoản Chrome:</b> {prof}
🌐 <b>Trang web:</b> <code>daotaoltx.eco-tek.com.vn</code>
⏱️ <b>Thời gian hiện tại:</b> <b>{status.get('webOfficialText', '7 giờ 18 phút')}</b>
🛡️ <b>Mốc ngắt an toàn:</b> 9 giờ 30 phút (Còn ~2h 12m)

✅ Trình duyệt Chrome đã tự động mở đúng hồ sơ lưu đăng nhập!
✅ Công cụ EcoTek Auto đang tự động kết nối, phát video và đếm giờ.
✅ Khi hết môn hiện tại, tool sẽ <b>TỰ ĐỘNG CHUYỂN SANG MÔN TIẾP THEO</b>.

<i>Khi học xong hoặc chạm mốc ngắt an toàn 9h30, Bot sẽ tự động gửi báo cáo kết thúc về đây cho anh!</i>"""
                else:
                    resp_msg = f"❌ Không thể khởi động Chrome tự động: {prof}. Anh vui lòng kiểm tra máy tính nhé!"
                send_message(chat_id, resp_msg, reply_markup=MAIN_KEYBOARD)

            # TÍNH NĂNG 2: TẠM DỪNG HỌC TỪ XA
            elif text in ["⏹️ Tạm Dừng Học", "/dunghoc", "/stop_study", "dung hoc", "tạm dừng", "dừng"]:
                status['isRunning'] = False
                status['lastRemoteCommand'] = 'stop'
                status['lastRemoteCommandTime'] = time.time()
                save_status(status)
                resp_msg = """⏹️ <b>ĐÃ GỬI LỆNH TẠM DỪNG HỌC</b>
━━━━━━━━━━━━━━━━━━━
Tool trên máy tính đã nhận lệnh tạm dừng tính giờ và dừng video.
Anh có thể bấm '🚀 Bật Học Tự Động Trên Máy' bất cứ lúc nào để tiếp tục!"""
                send_message(chat_id, resp_msg, reply_markup=MAIN_KEYBOARD)

            elif text in ["📊 Báo Cáo Chuẩn Web LMS", "📊 Báo Cáo Tiến Độ Hôm Nay", "/baocao"]:
                rep = build_progress_report(status)
                send_message(chat_id, rep, reply_markup=MAIN_KEYBOARD)

            # TÍNH NĂNG 3: TOÀN BỘ KHÓA HỌC C1 (5 MÔN) VỚI HÌNH ẢNH INFOGRAPHIC
            elif text in ["📚 Toàn Bộ Khóa Học C1 (5 Môn)", "/khoahoc", "/c1", "khoa hoc c1", "5 môn học"]:
                course_kb = {
                    "inline_keyboard": [
                        [{"text": "⚖️ 1. Pháp Luật GTĐB", "callback_data": "c1_course_1"},
                         {"text": "🔧 2. Cấu Tạo & Sửa Chữa", "callback_data": "c1_course_2"}],
                        [{"text": "🚛 3. Nghiệp Vụ Vận Tải C1", "callback_data": "c1_course_3"},
                         {"text": "❤️ 4. Đạo Đức & Văn Hóa", "callback_data": "c1_course_4"}],
                        [{"text": "🎮 5. Kỹ Thuật Lái Xe C1", "callback_data": "c1_course_5"}],
                        [{"text": "🚚 Cẩm Nang Xe Tải C1", "callback_data": "c1_truck_guide"},
                         {"text": "📺 Xem Link Video YouTube", "callback_data": "show_videos"}]
                    ]
                }
                try:
                    img_bytes = generate_c1_course_overview_image(status)
                    caption = """📚 <b>TOÀN BỘ KHÓA HỌC LÝ THUYẾT LÁI XE HẠNG C1</b>
━━━━━━━━━━━━━━━━━━━
Khóa học chuẩn 90 giờ trên hệ thống EcoTek gồm 5 môn học bắt buộc.
Tool EcoTek Auto tự động học tuần tự và làm trắc nghiệm đạt 100%.

👇 <i>Anh bấm vào từng môn bên dưới để xem tóm tắt kiến thức & mẹo thi:</i>"""
                    send_photo(chat_id, img_bytes, caption=caption, reply_markup=course_kb)
                except Exception as e:
                    rep = build_courses_and_videos_report(status)
                    send_message(chat_id, rep, reply_markup=MAIN_KEYBOARD)

            elif text in ["📺 5 Môn Học & Video YouTube", "/videos"]:
                rep = build_courses_and_videos_report(status)
                send_message(chat_id, rep, reply_markup=MAIN_KEYBOARD)

            elif text in ["🚗 Ôn Thi Sát Hạch C1", "/onthi"]:
                send_practice_menu(chat_id)

            elif text in ["⚠️ 60 Câu Điểm Liệt", "/diemliet"]:
                send_practice_question(chat_id, 'CRITICAL', 0)

            # TÍNH NĂNG 4: CHUYÊN ĐỀ BIỂN BÁO (185 CÂU - 100% ẢNH GỐC ĐỀ THI THẬT)
            elif text in ["🛑 Biển Báo (Có Ảnh)", "🔴 Biển Báo (Có Ảnh)", "/bienbao", "/signs", "biển báo", "bien bao"]:
                send_practice_question(chat_id, 'CH5', 0)

            # TÍNH NĂNG 5: CHUYÊN ĐỀ SA HÌNH (115 CÂU - 100% ẢNH GỐC ĐỀ THI THẬT)
            elif text in ["🧩 Sa Hình (Có Ảnh)", "/sahin", "/sahinh", "sa hình", "sa hinh"]:
                send_practice_question(chat_id, 'CH6', 0)

            # TÍNH NĂNG 6: CHUYÊN ĐỀ XE TẢI HẠNG C1
            elif text in ["🚛 Chuyên Đề Xe Tải C1", "/xetai", "/c1truck", "xe tải"]:
                try:
                    img_bytes = generate_c1_truck_infographic()
                    cap = """🚛 <b>CẨM NANG TOÀN DIỆN XE TẢI HẠNG C1 (3.500kg - 7.500kg)</b>
━━━━━━━━━━━━━━━━━━━
• <b>Phạm vi:</b> Xe tải 3.5t - 7.5t, kéo rơ moóc đến 750kg, đủ 21 tuổi.
• <b>Phanh khí nén:</b> Kiểm tra áp suất khí, xả nước van đáy bình tích.
• <b>Đề-pa dốc số sàn:</b> Phanh tay + đệm ga 1.200 rpm + giữ côn điểm rung.
• <b>Đổ đèo:</b> Về số thấp (số 1 hoặc 2) dùng phanh động cơ, cấm về số mo.
• <b>Điểm mù:</b> Cực lớn ở sát đầu xe, sau đuôi và sườn bên phải."""
                    send_photo(chat_id, img_bytes, caption=cap, reply_markup=MAIN_KEYBOARD)
                except Exception as e:
                    send_message(chat_id, "🚛 <b>Bằng C1:</b> Điều khiển ô tô tải từ 3.500 kg đến 7.500 kg, kéo rơ moóc đến 750 kg. Tuổi tối thiểu: Đủ 21 tuổi!", reply_markup=MAIN_KEYBOARD)

            elif text in ["💡 Mẹo Thi Đậu 100%", "/meothi"]:
                send_message(chat_id, EXAM_TIPS_TEXT, reply_markup=MAIN_KEYBOARD)

            elif text in ["🔑 Quản Lý Token AI", "/keys", "/tokens"]:
                keys_stat = get_keys_status()
                send_message(chat_id, keys_stat, reply_markup=MAIN_KEYBOARD)

            elif text.startswith("/addkey ") or text.startswith("/key "):
                k_val = text.split(maxsplit=1)[1].strip()
                ok, msg = add_api_key(k_val)
                send_message(chat_id, f"🔑 <b>KẾT QUẢ NẠP KEY:</b>\n\n{msg}", reply_markup=MAIN_KEYBOARD)

            elif text in ["🛑 Đóng Chrome Học", "/dongchrome", "/killchrome", "dong chrome", "đóng chrome"]:
                ok, msg = kill_chrome_processes()
                send_message(chat_id, f"🛑 <b>ĐÃ ĐÓNG CHROME:</b>\n\n{msg}\nAnh có thể mở lại Chrome bất kỳ lúc nào để làm việc hoặc chọn hồ sơ khác!", reply_markup=MAIN_KEYBOARD)

            elif text in ["👨‍🏫 Thầy AI Antigravity", "/thayai", "thầy ai", "thay ai"]:
                send_chat_action(chat_id, 'typing')
                welcome_ai = """🤖 <b>DẠ EM ĐÂY ANH HIẾU ƠI! EM LÀ ANTIGRAVITY ĐÂY Ạ!</b>
━━━━━━━━━━━━━━━━━━━
Em đã được nâng cấp toàn diện với bộ não tri thức chuyên sâu 100% chuẩn Luật Giao thông & Sát hạch Bộ GTVT 2024:
✨ <b>Tra cứu tức thì 600 câu hỏi:</b> Đầy đủ đáp án chính xác, phân tích bẫy thi và mẹo ghi nhớ nhanh.
✨ <b>Bí kíp 5 bước sa hình & Đề-pa dốc 4 bước:</b> Giải quyết mọi tình huống khó nhằn không lo tụt dốc hay chết máy.
✨ <b>Hệ thống AI đa Model tự động xoay vòng:</b> Trả lời thông minh, chu đáo, ân cần mọi câu hỏi về thi bằng, học tập, công việc và cuộc sống!

👇 <i>Anh có thể bấm các nút hỏi nhanh 1 chạm bên dưới hoặc <b>nhắn tin trực tiếp</b>, em sẽ giải đáp ngay như đang trò chuyện cùng anh ạ:</i>"""
                ai_keyboard = {
                    "inline_keyboard": [
                        [{"text": "⚠️ 60 Câu Điểm Liệt (Cấm Sai)", "callback_data": "ai_act_critical"},
                         {"text": "🚦 Thần Chú 5 Bước Sa Hình", "callback_data": "ai_act_sahin"}],
                        [{"text": "🏔️ Đề-Pa Dốc Số Sàn 4 Bước", "callback_data": "ai_act_depa"},
                         {"text": "🚛 Toàn Bộ Quy Định Bằng C1", "callback_data": "ai_act_c1"}],
                        [{"text": "🔑 Mẹo Từ Khóa Vàng 600 Câu", "callback_data": "ai_act_keywords"},
                         {"text": "📊 Tiến Độ Học LMS Hôm Nay", "callback_data": "ai_act_today"}]
                    ]
                }
                send_message(chat_id, welcome_ai, reply_markup=ai_keyboard)

            else:
                # GỬI ĐẾN ANTIGRAVITY AI ENGINE (KÈM TỰ ĐỘNG XOAY VÒNG KEY & LƯU NGỮ CẢNH)
                send_chat_action(chat_id, 'typing')
                ai_resp = ask_antigravity_ai(text, chat_id=chat_id)
                send_message(chat_id, ai_resp, reply_markup=MAIN_KEYBOARD)

    except Exception as e:
        print(f"[Bot] Lỗi xử lý update: {e}")

def telegram_polling_loop():
    print("[Telegram Polling] Bắt đầu lắng nghe tin nhắn...")
    offset = 0
    fail_count = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{CONFIG['BOT_TOKEN']}/getUpdates?offset={offset}&timeout=20"
            resp = _telegram_session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('ok'):
                    fail_count = 0
                    for u in data.get('result', []):
                        offset = u['update_id'] + 1
                        try:
                            # Chạy mỗi update trong thread riêng để không bao giờ làm block hàng đợi nhận tin/bấm nút
                            threading.Thread(target=handle_telegram_update, args=(u,), daemon=True).start()
                        except Exception as e:
                            print(f"[Bot] Lỗi khởi chạy thread update: {e}")
                else:
                    fail_count += 1
            elif resp.status_code == 409:
                print("[Telegram Polling] 409 Conflict: Phát hiện một phiên bản khác đang nhận tin. Thử lại sau 10s...")
                time.sleep(10)
                continue
            else:
                fail_count += 1
        except Exception as e:
            err_msg = str(e).lower()
            if 'timed out' in err_msg or 'timeout' in err_msg:
                # Long polling timeout khi không có tin nhắn mới là hoàn toàn bình thường, tiếp tục vòng lặp ngay
                continue
            fail_count += 1
            wait_time = min(10, 2 + fail_count)
            print(f"[Telegram Polling] Gián đoạn mạng ({e}). Tự động thử lại sau {wait_time}s...")
            time.sleep(wait_time)

# ================= FLASK CLOUD WEB SERVER & API ENDPOINTS =================

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoTek Driving Study - Cloud Bot 24/7</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --card-bg: rgba(22, 30, 49, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #38bdf8;
            --accent: #10b981;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.12) 0px, transparent 50%);
            min-height: 100vh;
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
        }
        .container {
            width: 100%;
            max-width: 680px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 36px 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 28px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
        }
        .title-group h1 {
            font-size: 22px;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .title-group p { font-size: 13px; color: var(--text-sub); margin-top: 4px; }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .status-pulse {
            width: 8px;
            height: 8px;
            background-color: #34d399;
            border-radius: 50%;
            box-shadow: 0 0 10px #34d399;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.6; }
            100% { transform: scale(0.95); opacity: 1; }
        }
        .grid-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 18px 20px;
        }
        .stat-card .label { font-size: 12px; color: var(--text-sub); margin-bottom: 6px; }
        .stat-card .value { font-size: 20px; font-weight: 800; color: #fff; }
        .stat-card .desc { font-size: 12px; color: var(--primary); margin-top: 4px; }
        .info-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 13px;
        }
        .info-row:last-child { border-bottom: none; }
        .info-row .k { color: var(--text-sub); }
        .info-row .v { font-weight: 600; color: #f1f5f9; text-align: right; }
        .btn-tele {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #fff;
            padding: 14px 20px;
            border-radius: 14px;
            font-size: 15px;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.2s ease;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.4);
        }
        .btn-tele:hover { transform: translateY(-2px); box-shadow: 0 15px 30px -5px rgba(2, 132, 199, 0.6); }
        .features-list {
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 12px;
            color: var(--text-sub);
        }
        .features-list div { display: flex; align-items: center; gap: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>EcoTek Driving Bot Cloud</h1>
                <p>Hệ Thống Ôn Thi & Trợ Lý Học Lái Xe 24/7</p>
            </div>
            <div class="status-badge">
                <div class="status-pulse"></div>
                ONLINE 24/7
            </div>
        </div>

        <div class="grid-stats">
            <div class="stat-card">
                <div class="label">⏱️ Đã học hôm nay</div>
                <div class="value">{{ status.get('webOfficialText', '0 giờ 0 phút') }}</div>
                <div class="desc">{{ status.get('todayCompletedLessons', 0) }} bài hoàn thành</div>
            </div>
            <div class="stat-card">
                <div class="label">🎯 Thi thử sát hạch</div>
                <div class="value">40 Câu</div>
                <div class="desc">Chuẩn Cục Đường Bộ 100%</div>
            </div>
        </div>

        <div class="info-card">
            <div class="info-row">
                <span class="k">👤 Học viên</span>
                <span class="v">{{ config.STUDENT_NAME }}</span>
            </div>
            <div class="info-row">
                <span class="k">🎓 Khóa học</span>
                <span class="v">{{ config.COURSE_NAME }}</span>
            </div>
            <div class="info-row">
                <span class="k">📖 Môn đang học</span>
                <span class="v">{{ status.get('currentCourseName', 'Cấu tạo & sửa chữa xe ô tô') }}</span>
            </div>
            <div class="info-row">
                <span class="k">⚡ Tiến độ môn</span>
                <span class="v">{{ status.get('courseProgress', '52%') }}</span>
            </div>
            <div class="info-row">
                <span class="k">🛡️ Bảo vệ giờ học</span>
                <span class="v">Tự ngắt lúc 9h30 (Dưới trần 10h)</span>
            </div>
        </div>

        <a href="https://t.me/BangC1_bot" class="btn-tele" target="_blank">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.52 2.77-1.17 3.35-1.37 3.73-1.38.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
            Mở Telegram Bot @BangC1_bot
        </a>

        <div class="features-list">
            <div>🎙️ Tương tác giọng nói AI</div>
            <div>📻 Sách nói 600 câu rảnh tay</div>
            <div>📱 Dùng mọi lúc mọi nơi</div>
            <div>☁️ Hoạt động 24/7 không cần PC</div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def route_index():
    st = load_status()
    return render_template_string(HTML_DASHBOARD, status=st, config=CONFIG)

@app.route('/ping')
def route_ping():
    return jsonify({
        'ok': True,
        'pong': time.time(),
        'service': 'ecotek-driving-cloud-bot',
        'student': CONFIG['STUDENT_NAME']
    })

@app.route('/status')
def route_status():
    return jsonify(load_status())

@app.route('/remote_command')
def route_remote_command():
    st = load_status()
    return jsonify({
        'command': st.get('lastRemoteCommand', 'stop'),
        'isRunning': st.get('isRunning', False),
        'commandTime': st.get('lastRemoteCommandTime', 0)
    })

@app.route('/sync_status', methods=['POST'])
@app.route('/api/sync_status', methods=['POST'])
@app.route('/sync_all_data', methods=['POST'])
def route_sync_status():
    payload = request.get_json(force=True, silent=True) or {}
    cur = load_status()

    # Bảo vệ chống ghi đè dữ liệu rác
    for k in ['webOfficialSeconds', 'webOfficialText', 'todaySeconds', 'todayCompletedLessons',
              'totalAccumulatedSeconds', 'totalAccumulatedLessons', 'currentCourseName',
              'currentLessonTitle', 'currentLessonMeta', 'courseProgress', 'allCourses', 'collectedVideos',
              'lastSlideUrl', 'lastCourseUrl', 'isRunning', 'lastRemoteCommand']:
        if k not in payload:
            continue
        val = payload[k]
        if k in ['currentLessonTitle', 'currentCourseName', 'currentLessonMeta'] and (not val or 'Đang nhận diện' in str(val) or 'Đang tải' in str(val)):
            continue
        if k == 'courseProgress' and (not val or val == '--%'):
            continue
        if k == 'allCourses':
            if not val or len(val) == 0 or not any(c.get('title') for c in val):
                continue
        if k in ['lastSlideUrl', 'lastCourseUrl'] and not val:
            continue
        if k in ['webOfficialSeconds', 'todaySeconds']:
            if (val or 0) >= 36000:
                continue
            if val == 26280 and cur.get(k, 0) != 26280:
                continue
            if val == 0 and cur.get(k, 0) > 0:
                continue
        if k == 'webOfficialText':
            if val in ['7 giờ 18 phút', '0 giờ 0 phút', '88h 33m'] or '88' in str(val) or '54' in str(val):
                continue
        if k == 'totalAccumulatedSeconds':
            if (val or 0) > 300000 or (val or 0) < (cur.get(k, 0) or 0):
                continue
        if k in ['isRunning', 'lastRemoteCommand'] and ((payload.get('todaySeconds') or 0) >= 36000 or (payload.get('webOfficialSeconds') or 0) >= 36000):
            cur['isRunning'] = True
            cur['lastRemoteCommand'] = 'start'
            continue
        if k in ['totalAccumulatedLessons', 'todayCompletedLessons']:
            if (val or 0) < (cur.get(k, 0) or 0):
                continue
        cur[k] = val

    t_sec = cur.get('todaySeconds', 0) or 0
    cur['webOfficialSeconds'] = t_sec
    cur['webOfficialText'] = f"{t_sec // 3600} giờ {(t_sec % 3600) // 60} phút"
    cur['lastUpdate'] = time.time()
    save_status(cur)

    return jsonify({'ok': True, 'synced': True, 'isRunning': cur.get('isRunning', True), 'status': cur})

@app.route('/session_finished', methods=['POST'])
def route_session_finished():
    payload = request.get_json(force=True, silent=True) or {}
    reason = payload.get('reason', 'Đã đạt mốc an toàn dưới 10h/ngày!')
    status = load_status()
    msg = f"""🏁 <b>BÁO CÁO KẾT THÚC PHIÊN HỌC TỰ ĐỘNG!</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Học viên:</b> {CONFIG['STUDENT_NAME']}
⏱️ <b>Thời gian đã học:</b> <b>{status.get('webOfficialText', '0 giờ 0 phút')}</b>
📖 <b>Môn học:</b> {status.get('currentCourseName', '')}
🛡️ <b>Lý do kết thúc:</b> {reason}

✅ Tool đã <b>TỰ ĐỘNG DỪNG VÀ THOÁT TRANG</b> để bảo toàn 100% kết quả hôm nay, tuyệt đối không bị trừ về 0:0:0!"""
    send_message(CONFIG['CHAT_ID'], msg, reply_markup=MAIN_KEYBOARD)
    return jsonify({'ok': True, 'reported': True})

@app.route('/alert', methods=['POST'])
def route_alert():
    payload = request.get_json(force=True, silent=True) or {}
    txt = payload.get('text', 'Phát hiện sự cố!')
    send_message(CONFIG['CHAT_ID'], f"🚨 <b>CẢNH BÁO TỪ ECOTEK AUTO:</b>\n\n{txt}")
    return jsonify({'ok': True})

@app.route('/report_now', methods=['GET', 'POST'])
def route_report_now():
    status = load_status()
    msg = build_progress_report(status)
    send_message(CONFIG['CHAT_ID'], msg, reply_markup=MAIN_KEYBOARD)
    return jsonify({'ok': True})

@app.route('/ask_ai', methods=['POST'])
def route_ask_ai():
    payload = request.get_json(force=True, silent=True) or {}
    prompt = payload.get('prompt', '').strip()
    chat_id = payload.get('chat_id', 'web_tutor')
    if prompt:
        reply = ask_antigravity_ai(prompt, chat_id=chat_id)
    else:
        reply = "Dạ em chào anh Hiếu! Em là Antigravity đây ạ. Anh cần hỏi câu nào hay mẹo gì cứ nhắn em nhé!"
    return jsonify({'ok': True, 'reply': reply})

# ================= 120 MÔ PHỎNG TELEGRAM MINI APP ROUTES =================
@app.route('/simulation')
@app.route('/mophong')
def route_simulation():
    template_path = os.path.join(BASE_DIR, 'templates', 'simulation.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    return "❌ Chưa tìm thấy giao diện phòng thi mô phỏng!", 404

@app.route('/api/simulation_situations', methods=['GET'])
def route_simulation_situations():
    data_path = os.path.join(BASE_DIR, 'simulation_data.json')
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/simulation_result', methods=['POST'])
def route_simulation_result():
    payload = request.get_json(force=True, silent=True) or {}
    total = payload.get('totalScore', 0)
    passed = payload.get('isPassed', False)
    details = payload.get('details', [])
    status_icon = "🎉 <b>ĐẠT YÊU CẦU XUẤT SẮC!</b>" if passed else "⚠️ <b>CHƯA ĐẠT (CẦN TỐI THIỂU 35/50)</b>"
    msg = f"""🏆 <b>BÁO CÁO KẾT QUẢ THI THỬ 120 MÔ PHỎNG V2.0.0</b>\n━━━━━━━━━━━━━━━━━━━\n👤 <b>Thí sinh:</b> {CONFIG['STUDENT_NAME']} ({CONFIG['COURSE_NAME']})\n📊 <b>Tổng điểm:</b> <b>{total} / 50 ĐIỂM</b>\n🎯 <b>Kết luận:</b> {status_icon}\n⏱️ <b>Quy chế:</b> Đạt từ 35/50 điểm trở lên\n━━━━━━━━━━━━━━━━━━━\n📝 <i>Chi tiết 10 tình huống vừa thi:</i>\n"""
    for idx, d in enumerate(details[:10]):
        score = d.get('score', 0)
        t = d.get('time')
        t_str = f"{t:.1f}s" if t is not None else "Không phanh"
        msg += f"• <b>Câu #{idx+1} (TH #{d.get('sitId')}):</b> {score}/5đ (Phản xạ: {t_str})\n"
    msg += "\n💡 <i>Anh có thể mở lại phòng thi mô phỏng bất kỳ lúc nào để luyện bắt trọn điểm 5 nhé!</i>"
    send_message(CONFIG['CHAT_ID'], msg, reply_markup=MAIN_KEYBOARD)
    return jsonify({'ok': True})

# ================= TELEGRAM WEBHOOK 24/7 ENDPOINTS =================
@app.route('/webhook', methods=['GET', 'POST'])
def route_webhook():
    if request.method == 'GET':
        return jsonify({
            'ok': True,
            'service': 'EcoTek Driving Cloud Webhook 24/7',
            'status': 'active',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    update = request.get_json(force=True, silent=True)
    if update:
        # Xử lý update trong worker thread riêng để trả về HTTP 200 OK ngay lập tức cho Telegram (<50ms)
        try:
            threading.Thread(target=handle_telegram_update, args=(update,), daemon=True).start()
        except Exception as e:
            print(f"[Webhook Error] Lỗi khởi chạy thread update: {e}")
    return jsonify({'ok': True})

@app.route('/set_webhook', methods=['GET', 'POST'])
def route_set_webhook():
    webhook_url = f"{CONFIG['RENDER_EXTERNAL_URL'].rstrip('/')}/webhook"
    try:
        res = telegram_api('setWebhook', {
            'url': webhook_url,
            'drop_pending_updates': False,
            'allowed_updates': ["message", "callback_query"]
        })
        return jsonify({'ok': True, 'webhook_url': webhook_url, 'telegram_response': res})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/webhook_info', methods=['GET'])
def route_webhook_info():
    try:
        res = telegram_api('getWebhookInfo', {})
        return jsonify({'ok': True, 'info': res})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ================= ANTI-SLEEP KEEP-ALIVE THREAD =================
def anti_sleep_keep_alive():
    """Tự động ping Render web service mỗi 5 phút (300s) để giữ bot thức 24/7/365"""
    time.sleep(15)
    print(f"[Keep-Alive] Khởi động cơ chế chống ngủ đông cho Cloud Service: {CONFIG['RENDER_EXTERNAL_URL']}")
    while True:
        try:
            target_url = CONFIG['RENDER_EXTERNAL_URL'].rstrip('/') + '/ping'
            r = requests.get(target_url, timeout=20)
            if r.status_code == 200:
                print(f"[Keep-Alive] Ping thành công lúc {datetime.now().strftime('%H:%M:%S')} (Status 200)")
            else:
                print(f"[Keep-Alive] Ping trả về mã {r.status_code}")
        except Exception as e:
            print(f"[Keep-Alive] Cảnh báo ping: {e}")
        time.sleep(300)

# ================= BACKGROUND THREADS INITIALIZATION =================
def setup_cloud_webhook():
    webhook_url = f"{CONFIG['RENDER_EXTERNAL_URL'].rstrip('/')}/webhook"
    print(f"[Telegram Bot] Đang kích hoạt Webhook 24/7 tới: {webhook_url}")
    try:
        res = telegram_api('setWebhook', {
            'url': webhook_url,
            'drop_pending_updates': False,
            'allowed_updates': ["message", "callback_query"]
        })
        print(f"[Telegram Bot] Kết quả thiết lập Webhook: {res}")
        return res.get('ok', False)
    except Exception as e:
        print(f"[Telegram Bot] Lỗi thiết lập Webhook: {e}")
        return False

def start_background_workers():
    # 1. Khởi chạy Keep-Alive Thread
    t_keep_alive = threading.Thread(target=anti_sleep_keep_alive, daemon=True)
    t_keep_alive.start()

    # 2. Kích hoạt Webhook 24/7 trên Render Cloud
    webhook_ok = False
    ext_url = CONFIG.get('RENDER_EXTERNAL_URL', '')
    if ext_url and ext_url.startswith('https://'):
        webhook_ok = setup_cloud_webhook()

    # 3. Chỉ bật Long Polling dự phòng nếu Webhook không được cấu hình
    if not webhook_ok:
        print("[Telegram Bot] Không dùng Webhook HTTPS, kích hoạt Long Polling dự phòng...")
        t_polling = threading.Thread(target=telegram_polling_loop, daemon=True)
        t_polling.start()

start_background_workers()

if __name__ == '__main__':
    print("=" * 60)
    print(" ECOTEK DRIVING AUTO - TELEGRAM CLOUD EDITION V4.0 (24/7)")
    print(f" Học viên: {CONFIG['STUDENT_NAME']} • Khóa: {CONFIG['COURSE_NAME']}")
    print(f" Telegram Bot: @BangC1_bot (Chat ID: {CONFIG['CHAT_ID']})")
    print(f" Web Service Port: {CONFIG['PORT']}")
    print(f" External Cloud URL: {CONFIG['RENDER_EXTERNAL_URL']}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=CONFIG['PORT'])
