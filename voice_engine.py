# -*- coding: utf-8 -*-
"""
VOICE ENGINE CHO ECOTEK TELEGRAM BOT - TƯƠNG TÁC GIỌNG NÓI TOÀN DIỆN
- Text-to-Speech (TTS):
  + Đọc câu hỏi & các phương án lựa chọn (Sped-up 1.18x brisk & crisp).
  + TẠO TIN NHẮN GIỌNG RIÊNG: Đọc đáp án đúng & giải thích mẹo nhanh riêng biệt.
  + SÁCH NÓI / PODCAST RẢNH TAY: Đọc câu hỏi + ngắt nghỉ + đáp án chuẩn để Telegram tự động phát liên tiếp.
- Speech-to-Text (STT): Nhận diện giọng nói của học viên (Voice Note Telegram) qua Faster-Whisper.
- Semantic Intent Parsing: Tự động trích xuất đáp án và các khẩu lệnh điều hướng.
- Bộ nhớ Cache Audio: Tăng tốc phản hồi 0ms.
"""

import os
import sys
import re
import time
import threading
import subprocess
import unicodedata
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_CACHE_DIR = os.path.join(BASE_DIR, 'audio_cache')
QUESTIONS_AUDIO_DIR = os.path.join(AUDIO_CACHE_DIR, 'questions')
EXPLAIN_AUDIO_DIR = os.path.join(AUDIO_CACHE_DIR, 'explains')
PODCAST_AUDIO_DIR = os.path.join(AUDIO_CACHE_DIR, 'podcast')

os.makedirs(QUESTIONS_AUDIO_DIR, exist_ok=True)
os.makedirs(EXPLAIN_AUDIO_DIR, exist_ok=True)
os.makedirs(PODCAST_AUDIO_DIR, exist_ok=True)

# Khởi tạo Whisper Model
_whisper_model = None
_whisper_lock = threading.Lock()

def get_whisper_model():
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model
        try:
            from faster_whisper import WhisperModel
            print("[Voice Engine] Đang nạp mô hình nhận diện giọng nói Faster-Whisper (base)...")
            _whisper_model = WhisperModel('tiny', device='cpu', compute_type='int8')
            print("[Voice Engine] ✅ Mô hình Whisper đã sẵn sàng phục vụ anh Hiếu!")
            return _whisper_model
        except Exception as e:
            print(f"[Voice Engine] Lỗi tải Whisper base: {e}. Thử fallback sang tiny...")
            try:
                from faster_whisper import WhisperModel
                _whisper_model = WhisperModel('tiny', device='cpu', compute_type='int8')
                return _whisper_model
            except Exception as e2:
                print(f"[Voice Engine] Không thể nạp Faster-Whisper: {e2}")
                return None

def preload_whisper_in_background():
    threading.Thread(target=get_whisper_model, daemon=True).start()

# ================= TỐC ĐỘ & LÀM SẠCH ÂM THANH =================

def speedup_audio_file(file_path, speed=1.18):
    """Tăng tốc độ đọc lên 1.18x bằng ffmpeg atempo giúp giọng đọc nhanh, tự nhiên, không rề rà"""
    if not os.path.exists(file_path):
        return file_path
    temp_out = file_path + ".tmp.mp3"
    try:
        cmd = ['ffmpeg', '-y', '-i', file_path, '-filter:a', f'atempo={speed}', '-vn', temp_out]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        if res.returncode == 0 and os.path.exists(temp_out) and os.path.getsize(temp_out) > 500:
            os.replace(temp_out, file_path)
    except Exception as e:
        print(f"[Voice Engine] Lỗi speedup audio: {e}")
        if os.path.exists(temp_out):
            try: os.remove(temp_out)
            except Exception: pass
    return file_path

def clean_text_for_speech(text):
    """Làm sạch HTML tags, icon và ký tự thừa để giọng đọc tự nhiên"""
    if not text:
        return ""
    t = re.sub(r'<[^>]+>', ' ', text)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# ================= 1. TIN NHẮN GIỌNG ĐỌC CÂU HỎI & CÁC ĐÁP ÁN =================

def build_question_speech_script(q_obj):
    """Soạn lời thoại đọc đề bài & các đáp án súc tích"""
    qid = q_obj.get('id', 1)
    q_text = clean_text_for_speech(q_obj.get('question', ''))
    is_crit = q_obj.get('isCritical', False)
    
    crit_alert = "Lưu ý, đây là câu điểm liệt. " if is_crit else ""
    speech = f"Câu {qid}. {crit_alert}{q_text}. "
    
    options = q_obj.get('options', [])
    for idx, opt in enumerate(options):
        opt_num = idx + 1
        opt_clean = clean_text_for_speech(opt)
        speech += f"Đáp án {opt_num}: {opt_clean}. "
        
    speech += "Mời anh chọn."
    return speech

def generate_question_audio(q_obj, force_regenerate=False):
    """Sinh file mp3 đọc câu hỏi & các đáp án (được tăng tốc nhẹ để nghe súc tích)"""
    qid = q_obj.get('id', 1)
    file_path = os.path.join(QUESTIONS_AUDIO_DIR, f"q_{qid}.mp3")
    
    if os.path.exists(file_path) and not force_regenerate and os.path.getsize(file_path) > 1000:
        return file_path
        
    speech_text = build_question_speech_script(q_obj)
    try:
        tts = gTTS(text=speech_text, lang='vi')
        tts.save(file_path)
        speedup_audio_file(file_path, speed=1.18)
        return file_path
    except Exception as e:
        print(f"[Voice Engine] Lỗi sinh giọng đọc câu {qid}: {e}")
        return None

# ================= 2. TIN NHẮN GIỌNG RIÊNG: ĐÁP ÁN ĐÚNG & MẸO GIẢI =================

def build_explanation_speech_script(q_obj):
    """Soạn lời thoại riêng biệt cho đáp án đúng và mẹo giải nhanh"""
    qid = q_obj.get('id', 1)
    ans = q_obj.get('answer', 1)
    opts = q_obj.get('options', [])
    correct_text = clean_text_for_speech(opts[ans - 1]) if ans <= len(opts) else ""
    raw_exp = clean_text_for_speech(q_obj.get('explanation', ''))
    
    # Cắt gọn phần giải thích nếu quá dài để người nghe dễ tiếp thu
    if len(raw_exp) > 250:
        raw_exp = raw_exp[:250] + "..."
        
    script = f"Đáp án chuẩn của Câu {qid} là Đáp án {ans}: {correct_text}. {raw_exp}"
    return script

def generate_explanation_audio(q_obj, force_regenerate=False):
    """Sinh file tin nhắn giọng riêng biệt đọc ĐÁP ÁN ĐÚNG & MẸO GIẢI"""
    qid = q_obj.get('id', 1)
    file_path = os.path.join(EXPLAIN_AUDIO_DIR, f"exp_{qid}.mp3")
    
    if os.path.exists(file_path) and not force_regenerate and os.path.getsize(file_path) > 1000:
        return file_path
        
    speech_text = build_explanation_speech_script(q_obj)
    try:
        tts = gTTS(text=speech_text, lang='vi')
        tts.save(file_path)
        speedup_audio_file(file_path, speed=1.18)
        return file_path
    except Exception as e:
        print(f"[Voice Engine] Lỗi sinh giọng giải thích câu {qid}: {e}")
        return None

# ================= 3. SÁCH NÓI / PODCAST RẢNH TAY (TỰ ĐỘNG PHÁT LIÊN TỤC) =================

def build_podcast_script(q_obj):
    """
    Soạn lời thoại podcast hoàn chỉnh:
    Đọc câu hỏi -> Các đáp án -> Nghỉ ngắn -> Đọc đáp án đúng và mẹo nhớ!
    """
    qid = q_obj.get('id', 1)
    q_text = clean_text_for_speech(q_obj.get('question', ''))
    is_crit = q_obj.get('isCritical', False)
    ans = q_obj.get('answer', 1)
    opts = q_obj.get('options', [])
    correct_text = clean_text_for_speech(opts[ans - 1]) if ans <= len(opts) else ""
    raw_exp = clean_text_for_speech(q_obj.get('explanation', ''))
    if len(raw_exp) > 200:
        raw_exp = raw_exp[:200]
        
    crit_tag = "Câu điểm liệt: " if is_crit else ""
    script = f"Câu {qid}. {crit_tag}{q_text}. "
    for idx, opt in enumerate(opts):
        script += f"Ý {idx + 1}: {clean_text_for_speech(opt)}. "
    script += f"Hết. ... ... Đáp án đúng: Ý {ans}: {correct_text}. Mẹo nhớ: {raw_exp}"
    return script

def generate_podcast_audio(q_obj, force_regenerate=False):
    """Sinh file audio podcast chuyên dụng để Telegram tự động phát liên tục từ câu này sang câu khác"""
    qid = q_obj.get('id', 1)
    file_path = os.path.join(PODCAST_AUDIO_DIR, f"pod_{qid}.mp3")
    
    if os.path.exists(file_path) and not force_regenerate and os.path.getsize(file_path) > 1000:
        return file_path
        
    script = build_podcast_script(q_obj)
    try:
        tts = gTTS(text=script, lang='vi')
        tts.save(file_path)
        speedup_audio_file(file_path, speed=1.20) # 1.20x tốc độ chuẩn nghe sách nói
        return file_path
    except Exception as e:
        print(f"[Voice Engine] Lỗi sinh podcast câu {qid}: {e}")
        return None

# ================= 4. GIỌNG NÓI TÙY CHỈNH & PHẢN HỒI THẦY AI =================

def generate_custom_speech(text, cache_name=None):
    """Sinh file mp3 cho lời giải thích, phản hồi hoặc câu trả lời của Thầy AI"""
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return None
        
    if cache_name:
        safe_name = re.sub(r'[^\w\-]', '_', cache_name)[:30]
        file_path = os.path.join(EXPLAIN_AUDIO_DIR, f"{safe_name}.mp3")
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
            return file_path
    else:
        file_path = os.path.join(EXPLAIN_AUDIO_DIR, f"temp_{int(time.time()*1000)}.mp3")
        
    try:
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "... Anh hãy xem thêm chi tiết trong tin nhắn nhé!"
        tts = gTTS(text=clean_text, lang='vi')
        tts.save(file_path)
        speedup_audio_file(file_path, speed=1.18)
        return file_path
    except Exception as e:
        print(f"[Voice Engine] Lỗi sinh custom speech: {e}")
        return None

# ================= 5. NHẬN DIỆN GIỌNG NÓI (SPEECH-TO-TEXT) =================

def transcribe_voice_file(audio_path):
    """Chuyển đổi file âm thanh sang văn bản tiếng Việt bằng Faster-Whisper"""
    model = get_whisper_model()
    if not model:
        return ""
    try:
        segments, info = model.transcribe(audio_path, language='vi')
        result_text = " ".join([s.text for s in segments]).strip()
        print(f"[Voice Engine] STT nhận diện ({info.language_probability:.2f}): \"{result_text}\"")
        return result_text
    except Exception as e:
        print(f"[Voice Engine] Lỗi transcribe voice file: {e}")
        return ""

# ================= 6. PHÂN TÍCH Ý ĐỊNH BẰNG GIỌNG NÓI =================

NUM_WORDS = {
    'một': 1, 'mốt': 1, 'nhất': 1, 'mot': 1, '1': 1,
    'hai': 2, 'nhì': 2, '2': 2,
    'ba': 3, 'tam': 3, '3': 3,
    'bốn': 4, 'tư': 4, 'bon': 4, '4': 4,
    'a': 1, 'b': 2, 'c': 3, 'd': 4
}

def remove_vietnamese_diacritics(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.replace('đ', 'd').replace('Đ', 'D')

def parse_voice_command(speech_text, active_question=None):
    """Phân tích lệnh giọng nói của học viên"""
    if not speech_text:
        return {'type': 'unknown', 'raw': ''}
        
    s = speech_text.lower().strip()
    s_nodot = re.sub(r'[\.,\?!]', '', s)
    num_opts = len(active_question.get('options', [])) if active_question else 4
    
    # 1. Chọn đáp án theo số/chữ cái: 'đáp án 1', 'chọn 2', 'câu 3', 'ý 4', 'A', 'B'
    match = re.search(r'(?:đáp án|chọn|ý|câu|phương án|số|phần)\s*([1-4]|một|mốt|nhất|hai|nhì|ba|bốn|tư|a|b|c|d)\b', s_nodot)
    if match:
        val_str = match.group(1)
        val_num = NUM_WORDS.get(val_str)
        if val_num and 1 <= val_num <= num_opts:
            return {'type': 'answer', 'value': val_num, 'raw': speech_text, 'method': 'keyword'}

    tokens = re.findall(r'\b([1-4]|một|mốt|nhất|hai|nhì|ba|bốn|tư|[abcd])\b', s_nodot)
    if len(tokens) == 1:
        val_num = NUM_WORDS.get(tokens[0])
        if val_num and 1 <= val_num <= num_opts:
            return {'type': 'answer', 'value': val_num, 'raw': speech_text, 'method': 'single_number'}

    # 2. Chọn đáp án theo nội dung câu chữ (Semantic match)
    if active_question and active_question.get('options'):
        best_opt_idx = None
        best_score = 0
        s_clean = remove_vietnamese_diacritics(s_nodot)
        
        for idx, opt in enumerate(active_question['options']):
            opt_clean = remove_vietnamese_diacritics(opt.lower().strip())
            if (opt_clean in s_clean or s_clean in opt_clean) and len(s_clean) >= 4:
                score = len(s_clean) / max(len(opt_clean), 1)
                if score > best_score:
                    best_score = score
                    best_opt_idx = idx + 1
                    
            s_words = set(s_clean.split())
            opt_words = set(opt_clean.split())
            common_words = s_words.intersection(opt_words)
            if len(common_words) >= 2:
                overlap_ratio = len(common_words) / len(opt_words)
                if overlap_ratio > best_score:
                    best_score = overlap_ratio
                    best_opt_idx = idx + 1
                    
        if best_score >= 0.35 and best_opt_idx:
            return {'type': 'answer', 'value': best_opt_idx, 'raw': speech_text, 'method': 'content_match'}

    # 3. Điều hướng
    if any(k in s for k in ['tiếp theo', 'câu sau', 'câu kế', 'tiếp tục', 'qua câu', 'next']):
        return {'type': 'nav', 'value': 'next', 'raw': speech_text}
    if any(k in s for k in ['câu trước', 'quay lại', 'lùi lại', 'trở về', 'lại câu', 'prev']):
        return {'type': 'nav', 'value': 'prev', 'raw': speech_text}
    if any(k in s for k in ['ngẫu nhiên', 'random']):
        return {'type': 'nav', 'value': 'rand', 'raw': speech_text}
    if any(k in s for k in ['nộp bài', 'chấm điểm', 'kết thúc bài', 'hoàn thành bài']):
        return {'type': 'submit', 'raw': speech_text}
    if any(k in s for k in ['đọc lại', 'nghe lại', 'phát lại', 'đọc câu hỏi']):
        return {'type': 'repeat_audio', 'raw': speech_text}
    if any(k in s for k in ['đáp án đúng', 'nghe đáp án', 'giải thích đáp án', 'đọc đáp án']):
        return {'type': 'read_answer', 'raw': speech_text}
    if any(k in s for k in ['chỉ mẹo', 'mẹo câu này', 'giải thích', 'tại sao', 'lý do']):
        return {'type': 'tip', 'raw': speech_text}
    if any(k in s for k in ['sách nói', 'podcast', 'rảnh tay', 'nghe liên tục', 'tự chuyển']):
        return {'type': 'podcast', 'raw': speech_text}
    if any(k in s for k in ['bật giọng nói', 'tự động đọc', 'bật đọc']):
        return {'type': 'toggle_voice', 'value': True, 'raw': speech_text}
    if any(k in s for k in ['tắt giọng nói', 'tắt đọc', 'dừng đọc']):
        return {'type': 'toggle_voice', 'value': False, 'raw': speech_text}

    # 4. Trò chuyện Thầy AI
    return {'type': 'chat', 'value': speech_text, 'raw': speech_text}
