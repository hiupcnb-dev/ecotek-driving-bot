# -*- coding: utf-8 -*-
"""
ENGINE THI SÁT HẠCH LÝ THUYẾT & QUẢN LÝ ÔN TẬP BẰNG C1 / B2 / C
Mô phỏng 100% phòng thi sát hạch thực tế theo quy chuẩn Tổng cục Đường bộ Việt Nam:
- 40 câu hỏi / đề thi (Thời gian: 24 phút)
- Tiêu chuẩn ĐẠT: Đúng từ 36/40 câu trở lên & KHÔNG SAI CÂU ĐIỂM LIỆT
- Ma trận phân bổ câu hỏi chuẩn sát hạch
- Quản lý phiên thi của học viên (Mock Exam Session)
- Sổ tay câu sai (Mistakes Notebook)
- Kho mẹo thi lý thuyết 100% đậu
"""

import json
import os
import sys
import time
import random
from datetime import datetime

# Đảm bảo mã hóa UTF-8 tránh lỗi charmap cp1252 trên Windows/Console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.json')
if not os.path.exists(QUESTIONS_FILE):
    QUESTIONS_FILE = os.path.join(BASE_DIR, 'driving-theory-app', 'js', 'questions.json')
if not os.path.exists(QUESTIONS_FILE):
    parent_dir = os.path.dirname(BASE_DIR)
    alt = os.path.join(parent_dir, 'driving-theory-app', 'js', 'questions.json')
    if os.path.exists(alt):
        QUESTIONS_FILE = alt

MISTAKES_FILE = os.path.join(BASE_DIR, 'user_mistakes.json')

# Tải 600 câu hỏi
ALL_QUESTIONS = []
if os.path.exists(QUESTIONS_FILE):
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            ALL_QUESTIONS = json.load(f)
        print(f"[Exam Engine] Loaded {len(ALL_QUESTIONS)} questions from {QUESTIONS_FILE}")
    except Exception as e:
        print(f"[Exam Engine] Error loading questions.json: {e}")

# Quản lý phiên thi của từng chat_id
ACTIVE_EXAMS = {}

# Sổ tay câu sai
def load_user_mistakes(chat_id=None):
    if not os.path.exists(MISTAKES_FILE):
        return {}
    try:
        with open(MISTAKES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if chat_id:
                return data.get(str(chat_id), [])
            return data
    except Exception:
        return {} if not chat_id else []

def record_user_mistake(chat_id, qid):
    chat_key = str(chat_id)
    data = load_user_mistakes()
    user_list = data.get(chat_key, [])
    if qid not in user_list:
        user_list.append(qid)
        data[chat_key] = user_list
        try:
            with open(MISTAKES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def remove_user_mistake(chat_id, qid):
    chat_key = str(chat_id)
    data = load_user_mistakes()
    user_list = data.get(chat_key, [])
    if qid in user_list:
        user_list.remove(qid)
        data[chat_key] = user_list
        try:
            with open(MISTAKES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

# ================= 1. SINH ĐỀ THI SÁT HẠCH CHUẨN 40 CÂU =================
def generate_mock_exam(exam_id=None):
    """
    Tạo đề thi sát hạch chuẩn 40 câu theo ma trận Cục Đường bộ Việt Nam:
    - 1-2 câu điểm liệt (BẮT BUỘC ĐÚNG)
    - 8 câu Chương 1 (Khái niệm & Quy tắc)
    - 2 câu Chương 2 (Nghiệp vụ vận tải)
    - 1 câu Chương 3 (Văn hóa & Đạo đức)
    - 2 câu Chương 4 (Kỹ thuật lái xe)
    - 1 câu Chương 5 (Cấu tạo & Sửa chữa)
    - 12 câu Chương 6 (Biển báo đường bộ)
    - 12 câu Chương 7 (Sa hình giao thông)
    Tổng cộng: ĐÚNG 40 CÂU
    """
    if not ALL_QUESTIONS:
        return []

    # Nếu có exam_id cụ thể (Đề 1 đến Đề 15), dùng seed để cố định bộ đề
    rng = random.Random(exam_id * 2026 if exam_id else None)

    crits = [q for q in ALL_QUESTIONS if q.get('isCritical')]
    ch1 = [q for q in ALL_QUESTIONS if q.get('chapter') == 1 and not q.get('isCritical')]
    ch2 = [q for q in ALL_QUESTIONS if q.get('chapter') == 2 and not q.get('isCritical')]
    ch3 = [q for q in ALL_QUESTIONS if q.get('chapter') == 3 and not q.get('isCritical')]
    ch4 = [q for q in ALL_QUESTIONS if q.get('chapter') == 4 and not q.get('isCritical')]
    ch5 = [q for q in ALL_QUESTIONS if q.get('chapter') == 5 and not q.get('isCritical')] # Biển báo
    ch6 = [q for q in ALL_QUESTIONS if q.get('chapter') == 6 and not q.get('isCritical')] # Sa hình

    selected = []
    # 1-2 câu điểm liệt
    selected.extend(rng.sample(crits, min(2, len(crits))))
    # Phân bổ các chương: Ch1 (8), Ch2 (2), Ch3 (2), Ch4 (2), Ch5 (13 biển báo), Ch6 (11 sa hình)
    selected.extend(rng.sample(ch1, min(8, len(ch1))))
    selected.extend(rng.sample(ch2, min(2, len(ch2))))
    selected.extend(rng.sample(ch3, min(2, len(ch3))))
    selected.extend(rng.sample(ch4, min(2, len(ch4))))
    selected.extend(rng.sample(ch5, min(13, len(ch5))))
    selected.extend(rng.sample(ch6, min(11, len(ch6))))

    # Đảm bảo đủ 40 câu
    remaining_needed = 40 - len(selected)
    if remaining_needed > 0:
        unused = [q for q in ALL_QUESTIONS if q not in selected]
        selected.extend(rng.sample(unused, min(remaining_needed, len(unused))))

    # Xáo trộn thứ tự các câu trong đề
    rng.shuffle(selected)
    return selected[:40]

# ================= 2. QUẢN LÝ PHIÊN THI SÁT HẠCH CHO HỌC VIÊN =================
def start_exam_session(chat_id, exam_id=None):
    """Bắt đầu một phiên thi sát hạch mới (24 phút)"""
    exam_questions = generate_mock_exam(exam_id)
    session = {
        'chat_id': chat_id,
        'exam_id': exam_id or "Ngẫu nhiên",
        'start_time': time.time(),
        'duration_sec': 24 * 60,  # 24 phút
        'questions': exam_questions,
        'answers': {},  # { q_index (0..39): chosen_option (1..4) }
        'current_index': 0,
        'is_completed': False,
        'result': None
    }
    ACTIVE_EXAMS[chat_id] = session
    return session

def get_exam_session(chat_id):
    return ACTIVE_EXAMS.get(chat_id)

def submit_exam_session(chat_id):
    """Chấm điểm phiên thi sát hạch theo tiêu chuẩn Cục Đường bộ"""
    session = ACTIVE_EXAMS.get(chat_id)
    if not session:
        return None

    elapsed_sec = int(time.time() - session['start_time'])
    elapsed_min = elapsed_sec // 60
    elapsed_remain_sec = elapsed_sec % 60

    correct_count = 0
    failed_critical = False
    critical_failed_questions = []
    mistakes = []

    for idx, q in enumerate(session['questions']):
        chosen = session['answers'].get(idx)
        correct_ans = q.get('answer', 1)
        is_crit = q.get('isCritical', False)

        if chosen == correct_ans:
            correct_count += 1
            remove_user_mistake(chat_id, q['id'])
        else:
            mistakes.append({
                'index': idx + 1,
                'id': q['id'],
                'question': q['question'],
                'chosen': chosen,
                'correct': correct_ans,
                'options': q.get('options', []),
                'explanation': q.get('explanation', ''),
                'isCritical': is_crit
            })
            record_user_mistake(chat_id, q['id'])
            if is_crit:
                failed_critical = True
                critical_failed_questions.append(idx + 1)

    # Tiêu chuẩn sát hạch Hạng C1: Đạt tối thiểu 36/40 câu & KHÔNG ĐƯỢC SAI CÂU ĐIỂM LIỆT
    is_passed = (correct_count >= 36) and (not failed_critical)

    result = {
        'chat_id': chat_id,
        'exam_id': session['exam_id'],
        'total_questions': len(session['questions']),
        'correct_count': correct_count,
        'score_text': f"{correct_count}/{len(session['questions'])}",
        'is_passed': is_passed,
        'failed_critical': failed_critical,
        'critical_failed_questions': critical_failed_questions,
        'elapsed_time_text': f"{elapsed_min} phút {elapsed_remain_sec} giây",
        'mistakes': mistakes
    }

    session['is_completed'] = True
    session['result'] = result
    return result

# ================= 3. BỘ BÍ KÍP MẸO THI 100% ĐẬU (10 NHÓM MỚI TỪ 600 CÂU) =================
EXAM_TIPS_CATEGORIES = {
    'keywords': {
        'title': '🔑 1. Mẹo Từ Khóa Vàng (Bắt bài trong 3 giây - Chọn là trúng 100%)',
        'items': [
            ("Bị nghiêm cấm", "Cứ thấy phương án có cụm từ 'Bị nghiêm cấm' -> CHỌN NGAY đáp án đó (25 câu hỏi điểm liệt và câu luật đều đúng 100%).\n• Ví dụ: Đua xe, chạy quá tốc độ, lạng lách, uống rượu bia, ma túy, lùi xe trên cao tốc, giao xe cho người không đủ điều kiện..."),
            ("Không được phép / Tuyệt đối không", "Phương án có chứa 'Không được phép', 'Không được quay đầu', 'Không được mang vác', 'Không được lùi xe' -> CHỌN LUÔN đáp án đó (52 câu trong bộ 600 câu).\n• Ngoại lệ duy nhất: Xe ưu tiên làm nhiệm vụ được phép đi vào đường cấm (trừ đi ngược chiều trên cao tốc)."),
            ("Cơ quan có thẩm quyền cấp phép", "Các câu hỏi về thay đổi kết cấu tổng thành xe, đua xe, chở hàng quá tải quá khổ, vận chuyển chất nguy hiểm -> Luôn chọn đáp án có 'Được cơ quan có thẩm quyền cấp phép'."),
            ("Hiệu lệnh của Cảnh sát giao thông (CSGT)", "Tại nơi giao nhau có cả CSGT, đèn tín hiệu và biển báo -> BẮT BUỘC CHẤP HÀNH HIỆU LỆNH CỦA CSGT (Hiệu lệnh của CSGT cao nhất)."),
            ("Giảm tốc độ / Nhường đường / Đi về bên phải", "Gặp nguy hiểm, thời tiết xấu (mưa to, sương mù), qua giao lộ, gặp người đi bộ, trẻ em -> Luôn ưu tiên chọn đáp án có 'Giảm tốc độ', 'Đi về bên phải', 'Nhường đường'."),
            ("Về số thấp (Số 1 hoặc số 2)", "Đổ đèo dốc cao dài, leo dốc gắt, qua đường ngập nước, đường bùn lầy -> Luôn chọn đáp án có 'Về số thấp' (hoặc 'Về số 1') để tận dụng lực hãm động cơ và lực kéo lớn."),
            ("Mẹo các câu bắt đầu bằng từ 'Quan sát'", "Nếu câu hỏi có nhiều đáp án cùng bắt đầu bằng từ 'Quan sát' -> Hãy chọn đáp án DÀI NHẤT, có nội dung đầy đủ nhất (bao quát gương chiếu hậu, hai bên và phía sau).")
        ]
    },
    'numbers': {
        'title': '🔢 2. Mẹo Các Con Số Thần Thánh (Mét, Giờ, CPR - Bắt buộc thuộc lòng)',
        'items': [
            ("Số 5 (Mét) - Đường ray & Đỗ xe nối đuôi", "• Dừng xe trước đường ray tàu hỏa: TỐI THIỂU 5 MÉT tính từ ray ngoài cùng (khi có chuông reo/đèn đỏ).\n• Đỗ xe nối đuôi nhau cùng một phía đường phố: TỐI THIỂU 5 MÉT."),
            ("Số 0.25 (Mét) - Đỗ xe sát lề hè phố", "Khi dừng đỗ xe trên đường phố đô thị: Bánh xe gần nhất không được cách mép lề hè phố vượt quá 0.25 MÉT (25 cm)."),
            ("Số 20 (Mét) - Đỗ xe đường hẹp đối diện", "Khoảng cách an toàn giữa 2 xe ô tô đỗ đối diện nhau trên phố hẹp TỐI THIỂU LÀ 20 MÉT để tránh tắc đường."),
            ("Số 150 (Mét) - Đặt cảnh báo cao tốc", "Xe gặp sự cố dừng khẩn cấp trên cao tốc: Đặt biển/cọc tiêu cảnh báo phía sau xe TỐI THIỂU 150 MÉT để xe sau kịp phanh."),
            ("Số 4 Giờ & 10 Giờ - Thời gian lái xe", "• Lái xe liên tục: KHÔNG QUÁ 4 GIỜ.\n• Tổng thời gian làm việc trong ngày: KHÔNG QUÁ 10 GIỜ."),
            ("Tỷ lệ 30 : 2 - Cấp cứu CPR", "Sơ cứu ngừng tim ngừng thở: ÉP TIM 30 LẦN KẾT HỢP 2 LẦN THỔI NGẠT liên tục theo chu kỳ."),
            ("Âm lượng còi xe (90 - 115 dB)", "Đo cách đầu xe 2 mét: Âm lượng còi xe ô tô chuẩn từ 90 dB(A) đến 115 dB(A)."),
            ("Độ rơ vô lăng (10° - 15°)", "• Xe ô tô con: Độ rơ vô lăng KHÔNG QUÁ 10° - 15°.\n• Xe ô tô tải nặng: Độ rơ KHÔNG QUÁ 20° - 25°.")
        ]
    },
    'distances': {
        'title': '📏 3. Mẹo Cự Ly An Toàn Bậc Thang (35m - 55m - 70m - 100m)',
        'items': [
            ("Bảng cự ly an toàn đường khô ráo", "• Vận tốc = 60 km/h: 35 MÉT\n• 60 < Vận tốc ≤ 80 km/h: 55 MÉT\n• 80 < Vận tốc ≤ 100 km/h: 70 MÉT\n• 100 < Vận tốc ≤ 120 km/h: 100 MÉT\n💡 Mẹo nhớ nhanh: 35 -> 55 -> 70 -> 100."),
            ("Khi thời tiết xấu (Mưa bão, trơn trượt)", "Luôn chọn đáp án: 'Giữ cự ly an toàn LỚN HƠN khoảng cách tối thiểu ghi trên biển báo hoặc đường khô ráo'.")
        ]
    },
    'speed': {
        'title': '🏎️ 4. Mẹo Tốc Độ Trong & Ngoài Khu Dân Cư',
        'items': [
            ("Xe gắn máy (<50cc) & Xe máy điện", "Tốc độ tối đa KHÔNG QUÁ 40 KM/H trên TẤT CẢ các loại đường."),
            ("TRONG khu đông dân cư (Biển R.420)", "• Đường đôi (có dải phân cách giữa): Tối đa 60 KM/H.\n• Đường 2 chiều (không dải phân cách): Tối đa 50 KM/H."),
            ("NGOÀI khu đông dân cư (Mẹo đọc đuôi)", "1. Nhìn cuối đáp án: Thấy chữ 'xi-téc' hoặc 'bê-tông' -> CHỌN NGAY (100% đúng).\n2. Nếu không có 'xi-téc': Nhìn đầu đáp án -> Chọn đáp án có từ 'Ô tô con' đứng đầu tiên."),
            ("Tốc độ xe tải C1 (3.5t - 7.5t)", "• Ngoài khu dân cư - Đường đôi: Tối đa 80 KM/H.\n• Ngoài khu dân cư - Đường 2 chiều: Tối đa 70 KM/H.")
        ]
    },
    'ages': {
        'title': '🎂 5. Mẹo Độ Tuổi, Giấy Phép Lái Xe & Niên Hạn (+3 tuổi)',
        'items': [
            ("Công thức bậc thang độ tuổi (+3 tuổi)", "• 16 tuổi: Xe dưới 50 cm³.\n• 18 tuổi: Mô tô A1, A2 & Ô tô B1, B2 (đến 9 chỗ, tải < 3.5t).\n• 21 tuổi (18+3): Ô tô tải C1 (3.5t - 7.5t), hạng C (> 7.5t), kéo FB2.\n• 24 tuổi (21+3): Chở khách 10 - 30 chỗ (hạng D), container (hạng FC).\n• 27 tuổi (24+3): Khách > 30 chỗ (hạng E), xe kéo nối toa (hạng FE).\n⚠️ Tuổi tối đa lái xe khách hạng E: Nam 55 tuổi, Nữ 50 tuổi."),
            ("Phân biệt Bằng B1 vs B2 vs C1", "• B1 (Số tự động): KHÔNG ĐƯỢC hành nghề kinh doanh vận tải.\n• B2: ĐƯỢC PHÉP hành nghề kinh doanh vận tải.\n• C1 (Luật mới): Lái xe tải từ 3.500 kg đến 7.500 kg, rơ moóc ≤ 750 kg."),
            ("Mẹo Bằng F: 'C cọc - E em'", "• FC (C cọc): Xe đầu kéo sơ mi rơ moóc (container).\n• FE (E em): Xe ô tô khách nối toa."),
            ("Niên hạn xe ô tô", "• Xe tải chở hàng: 25 NĂM.\n• Xe chở người trên 9 chỗ: 20 NĂM.\n• Xe ô tô con dưới 9 chỗ: KHÔNG CÓ NIÊN HẠN.")
        ]
    },
    'signs': {
        'title': '🛑 6. Mẹo Nhận Diện Biển Báo Cấm & Hiệu Lệnh (QCVN 41)',
        'items': [
            ("Cấm nhỏ cấm lớn - Cấm lớn không cấm nhỏ", "Thứ tự: Xe con -> Xe khách -> Xe tải -> Máy kéo -> Container.\n• Cấm xe con: Cấm cả xe khách, tải, máy kéo, rơ moóc.\n• Cấm xe tải: Xe con & khách VẪN ĐƯỢC PHÉP ĐI.\n• Cấm tải: Máy kéo và rơ moóc BỊ CẤM."),
            ("Cấm rẽ trái vs Cấm quay đầu", "• CẤM RẼ TRÁI (P.123a): KHÔNG CẤM QUAY ĐẦU (được quay đầu).\n• CẤM QUAY ĐẦU (P.124a): KHÔNG CẤM RẼ TRÁI (được rẽ trái)."),
            ("Cấm dừng đỗ (X) vs Cấm đỗ (1 gạch)", "• Biển chữ X (P.130): CẤM CẢ DỪNG VÀ ĐỖ XE.\n• Biển 1 gạch chéo (P.131a): CHỈ CẤM ĐỖ (được dừng xe tạm thời).\n• Biển vạch I: Cấm đỗ ngày LẺ. Vạch II: Cấm đỗ ngày CHẴN."),
            ("Biển phụ khoảng cách mét", "• Số mét KHÔNG CÓ MŨI TÊN ('500m'): Còn 500m nữa mới tới.\n• Số mét CÓ MŨI TÊN HAI BÊN ('↑ 500m ↑'): Chiều dài phạm vi tác dụng của biển.")
        ]
    },
    'lines': {
        'title': '🛣️ 7. Mẹo Vạch Kẻ Đường & Đèn Tín Hiệu',
        'items': [
            ("Vàng Ngược - Trắng Cùng", "• Vạch VÀNG: Phân chia 2 chiều chạy NGƯỢC NHAU (đường 2 chiều).\n• Vạch TRẮNG: Phân chia các làn chạy CÙNG CHIỀU."),
            ("Đứt Được - Liền Cấm", "• Vạch NÉT ĐỨT: ĐƯỢC PHÉP ĐÈ VẠCH, chuyển làn khi an toàn.\n• Vạch NÉT LIỀN: TUYỆT ĐỐI CẤM ĐÈ VẠCH, cấm lấn làn."),
            ("Vạch Quả Trám (Hình thoi)", "Báo hiệu sắp đến nơi có vạch người đi bộ qua đường -> Giảm tốc độ."),
            ("Vạch Mắt Võng & Vạch Xương Cá", "• Vạch Mắt Võng tại ngã tư: VÙNG CẤM DỪNG XE (chống ùn tắc).\n• Vạch Xương Cá: Đảo giao thông trên đường, CẤM ĐÈ VẠCH hoặc dừng đỗ.")
        ]
    },
    'sahin': {
        'title': '🧩 8. Mẹo 5 Bước Xét Sa Hình Thần Tốc (100% Đúng)',
        'items': [
            ("5 Bước xét sa hình", "1. NHẤT CHỚM: Xe chớm qua vạch ngã tư đi trước nhất.\n2. NHÌ ƯU: HỎA -> QUÂN -> CÔNG -> THƯƠNG.\n3. TAM ĐƯỜNG: Xe trên đường ưu tiên (biển hình thoi I.401, biển tam giác to W.207) đi trước.\n4. TỨ HƯỚNG: Ngã tư cùng cấp: Bên phải trống đi trước.\n5. NGŨ RẼ: Rẽ phải -> Đi thẳng -> Rẽ trái."),
            ("Hiệu lệnh của CSGT", "• CSGT giơ 1 TAY ĐỨNG: TẤT CẢ DỪNG LẠI (trừ xe đã trong ngã tư).\n• CSGT DANG 2 TAY NGANG: Trước/sau dừng lại; Trái/phải được đi tất cả các hướng."),
            ("Vòng xuyến", "• CÓ biển vòng xuyến: Nhường đường xe bên TRÁI.\n• KHÔNG CÓ biển vòng xuyến: Nhường đường xe bên PHẢI."),
            ("Tránh dốc", "Xe đang XUỐNG DỐC phải nhường đường cho xe đang LÊN DỐC.")
        ]
    },
    'mechanic': {
        'title': '⚙️ 9. Mẹo Kỹ Thuật Lái Xe & Cấu Tạo Sửa Chữa (Hạng C1 / Số Sàn)',
        'items': [
            ("Số tự động (AT)", "Khẩu quyết: 'RỜI CHÂN GA LÀ RÀ CHÂN PHANH'. Chân trái đặt chết bệ nghỉ, chỉ dùng chân phải."),
            ("Đổ đèo dốc cao", "Về số thấp (số 1 hoặc 2), tận dụng phanh động cơ. TUYỆT ĐỐI CẤM về mo (N), CẤM tắt máy, CẤM đạp côn trôi dốc!"),
            ("Phanh ABS", "ĐẠP HẾT HÀNH TRÌNH VÀ GIỮ CHẶT CHÂN PHANH (không nhấp nhả), bình tĩnh đánh lái tránh vật cản."),
            ("Đường ngập nước", "Mực nước dưới nửa bánh; đi số 1, giữ đều ga; xe chết máy TUYỆT ĐỐI KHÔNG ĐỀ LẠI (tránh thủy kích)."),
            ("Nổ lốp khẩn cấp", "Giữ chặt vô lăng thẳng lái, nhả ga từ từ, bật đèn khẩn cấp, TUYỆT ĐỐI KHÔNG PHANH GẤP."),
            ("Phanh khí nén xe tải C1", "HÀNG NGÀY PHẢI XẢ NƯỚC đọng ở đáy bình tích khí để chống rỉ sét và kẹt van phanh.")
        ]
    },
    'firstaid': {
        'title': '🚑 10. Mẹo Sơ Cứu Y Tế TNGT & Tình Huống Khẩn Cấp',
        'items': [
            ("Sơ cứu Gãy xương", "Cố định nẹp BẤT ĐỘNG QUA 2 KHỚP LIỀN KỀ (khớp trên và dưới); TUYỆT ĐỐI KHÔNG tự ý kéo nắn xương."),
            ("Máu phun thành tia (Động mạch)", "Ấn ngón tay chặn đường đi động mạch; ĐẶT GA-RÔ PHÍA TRÊN VẾT THƯƠNG, ghi giờ đặt ga-rô và chuyển viện ngay."),
            ("Nằm nghiêng an toàn", "Nạn nhân hôn mê nhưng còn thở: Đặt NẰM NGHIÊNG SANG MỘT BÊN chống tụt lưỡi và chống sặc dịch đờm nôn."),
            ("Nồng độ cồn & Ma túy", "CẤM TUYỆT ĐỐI (nồng độ = 0). Phạt kịch khung ô tô 30-40 triệu, tước bằng lái 22-24 tháng.")
        ]
    },
    'lecture': {
        'title': '🎙️ 11. Mẹo Thực Chiến Từ Bài Giảng Ghi Âm Lớp Học (11/10/2026)',
        'items': [
            ("Cấu trúc đề thi sát hạch lý thuyết", "Đề chuẩn gồm 3 phần: Chữ (Khái niệm, Quy tắc, Đạo đức, Kỹ thuật, Sửa chữa) -> Biển báo -> Sa hình. Tiêu chuẩn C1: 36/40 câu đạt, KHÔNG ĐƯỢC SAI CÂU ĐIỂM LIỆT! Thầy dặn: Làm Biển báo và Sa hình trước để chắc điểm!"),
            ("Khái niệm Làn đường & Khổ giới hạn", "• 'Làn đường': Luôn tìm đáp án có cụm từ 'bề rộng đủ cho xe chạy an toàn' và chia theo chiều dọc.\n• 'Khổ giới hạn': Bắt buộc đáp án phải có cả 'chiều cao' và 'chiều rộng'."),
            ("Dải phân cách & Dừng xe vs Đỗ xe", "• Dải phân cách gồm: 'Cố định' và 'Di động'.\n• 'Dừng xe': Đứng yên TẠM THỜI CÓ GIỚI HẠN THỜI GIAN.\n• 'Đỗ xe': Đứng yên KHÔNG GIỚI HẠN THỜI GIAN."),
            ("2 Câu Ngoại Lệ của từ khóa Cấm", "99% thấy 'Bị nghiêm cấm' hay 'Không được phép' là chọn ngay, NHƯNG CÓ 2 CÂU NGOẠI LỆ ĐƯỢC VƯỢT:\n1. Gặp xe Cảnh sát/Công an chạy trước nhưng KHÔNG PHÁT TÍN HIỆU CÒI ĐÈN ƯU TIÊN -> ĐƯỢC PHÉP VƯỢT.\n2. Xe chuyên dùng, xe làm nhiệm vụ đặc biệt trên đường."),
            ("Đèn cảnh báo bảng táp-lô ô tô", "• Bật khóa điện ON: Các đèn sáng 2-3s tự kiểm tra. Khi nổ máy chạy: Đèn nào VẪN SÁNG ĐỎ/VÀNG là hệ thống đó ĐANG BỊ HỎNG/LỖI!\n• Đèn (!) hoặc (P): Phanh tay đang hãm hoặc thiếu dầu phanh.\n• Đèn bình dầu/ấm trà: Áp suất dầu bôi trơn thấp -> DỪNG XE NGAY LẬP TỨC để tránh bó vỡ lốc máy!"),
            ("Động cơ Diesel & Hệ thống bôi trơn", "• Động cơ Diesel KHÔNG DÙNG BUGI ĐÁNH LỬA (nhiên liệu tự cháy do nén khí cực cao).\n• Hệ thống bôi trơn: Cung cấp dầu bôi trơn sạch để giảm ma sát, làm mát, làm kín, làm sạch và chống rỉ sét."),
            ("Đỗ xe đường phố: 0.25m & 20m", "• Đỗ sát lề hè: Không cách quá 0.25 MÉT (25 cm).\n• Đỗ xe trên phố hẹp đối diện: Cách nhau tối thiểu 20 MÉT.\n• Thời gian lái xe: Liên tục không quá 4 GIỜ; tổng ngày không quá 10 GIỜ.")
        ]
    },
    'critical_60': {
        'title': '⚠️ 12. Mẹo 60 Câu Điểm Liệt (Chắc Chắn Đậu 100% - Không Bao Giờ Trượt Oan)',
        'items': [
            ("Tầm quan trọng của Câu Điểm Liệt", "Trong 40 câu sát hạch C1, chỉ cần SAI ĐÚNG 1 CÂU ĐIỂM LIỆT là TRƯỢT NGAY LẬP TỨC (Dù 39 câu còn lại đúng 100%)!\n• 100% câu điểm liệt là các tình huống gây tai nạn thảm khốc."),
            ("Mẹo 1: 'Bị nghiêm cấm' (25 câu)", "Cứ thấy cụm từ 'Bị nghiêm cấm' trong đáp án -> CHỌN NGAY:\n• Uống rượu bia, ma túy khi lái xe.\n• Đua xe, cổ vũ đua xe, lạng lách đánh võng.\n• Bấm còi hơi trong đô thị (22h - 5h sáng).\n• Phá hoại dải phân cách, cọc tiêu, gương cầu lồi."),
            ("Mẹo 2: 'Không được phép' (30 câu)", "Cứ thấy cụm từ 'Không được phép / Không được...' ở đầu đáp án -> CHỌN NGAY:\n• Không được lùi xe, quay đầu trên đường cao tốc.\n• Không được quay đầu trên cầu, gầm cầu vượt, trong hầm, nơi đường cong khuất tầm nhìn.\n• Không được vượt xe tại nơi đường sắt giao nhau hoặc tầm nhìn bị che khuất."),
            ("Mẹo 3: Khoảng cách đường ray 5 mét", "Tại nơi đường sắt giao nhau không có rào chắn, khi có chuông reo hoặc đèn đỏ nhấp nháy: BẮT BUỘC DỪNG CÁCH RAY NGOÀI CÙNG TỐI THIỂU 5 MÉT."),
            ("Mẹo 4: Xử lý xe mất phanh khi xuống dốc", "Luôn chọn đáp án: Về số thấp (số 1), dùng lực hãm động cơ, kéo phanh tay từ từ, tìm chướng ngại vật/hộc cứu nạn bên đường để dừng xe. TUYỆT ĐỐI CẤM về số mo (N) hoặc tắt máy!"),
            ("Mẹo 5: Hành vi khi gây tai nạn", "Phải dừng xe ngay tại hiện trường, giữ nguyên hiện trường, cấp cứu người bị thương và trình báo cơ quan công an. TUYỆT ĐỐI CẤM bỏ trốn để trốn tránh trách nhiệm.")
        ]
    },
    'trick_traps': {
        'title': '🎯 13. Mẹo Bắt Bài Câu Hỏi Gài Bẫy (Quy Tắc \'Cả Ý 1 & 2\', Ngoại Lệ)',
        'items': [
            ("Bẫy 'Cả ý 1 và ý 2' (Chỉ đúng trong 4 câu)", "Trong 600 câu mới, Bộ GTVT đã bỏ hầu hết đáp án 'Cả ý 1 và 2'. CHỈ CÒN ĐÚNG 4 CÂU ĐƯỢC CHỌN 'CẢ Ý 1 VÀ 2':\n1. Đạo đức kinh doanh vận tải.\n2. Hành vi bồi dưỡng kỹ năng lái xe.\n3. Xe vận chuyển hàng siêu trường, siêu trọng.\n4. Trách nhiệm của đơn vị kinh doanh vận tải.\n👉 Các câu khác thấy 'Cả ý 1 và 2' thường là BẪY SAI!"),
            ("Bẫy 'Xe cảnh sát / công an'", "• Xe Cảnh sát ĐANG PHÁT TÍN HIỆU ƯU TIÊN (còi, đèn nhấp nháy): TUYỆT ĐỐI KHÔNG ĐƯỢC VƯỢT.\n• Xe Cảnh sát KHÔNG PHÁT TÍN HIỆU ƯU TIÊN: ĐƯỢC PHÉP VƯỢT khi đảm bảo an toàn."),
            ("Bẫy 'Đi ngược chiều trên cao tốc'", "KỂ CẢ XE ƯU TIÊN (chữa cháy, công an) cũng TUYỆT ĐỐI KHÔNG ĐƯỢC đi ngược chiều trên làn đường một chiều của đường cao tốc!"),
            ("Bẫy 'Niên hạn xe con dưới 9 chỗ'", "Xe ô tô con dưới 9 chỗ ngồi (không kinh doanh) KHÔNG CÓ NIÊN HẠN SỬ DỤNG. Tuyệt đối không chọn 20 năm hay 25 năm!")
        ]
    },
    'special_sahin': {
        'title': '🧩 14. Mẹo Độc Chiêu Sa Hình Thần Tốc (Bắt Bài Trong 2 Giây)',
        'items': [
            ("Mẹo 'Xe Công An'", "Trong sa hình có xe Công An:\n• Nhìn vào các đáp án, nếu đáp án nào có cụm 'Xe công an...' đi đầu tiên -> CHỌN NGAY (95% trúng).\n• Ngoại lệ: Nếu có xe con đã lọt hẳn vào ngã tư trước (Nhất chớm) thì xe con đó đi trước xe công an."),
            ("Mẹo 'Xe con quay đầu'", "Xe con chỉ được quay đầu theo hướng vạch chỉ đường cho phép. Nếu mũi tên quay đầu ĐÈ VẠCH NGƯỜI ĐI BỘ hoặc ĐÈ VẠCH LIỀN -> BỊ COI LÀ VI PHẠM."),
            ("Mẹo Biển Bắt đầu đường ưu tiên (I.401)", "Xe nào đứng trước mặt biển hình thoi viền vàng (hoặc biển tam giác to có đường giao cắt nét nhỏ W.207) -> XE ĐÓ ĐƯỢC ĐI TRƯỚC HẾT."),
            ("Mẹo Biển Giao nhau với đường ưu tiên (W.208)", "Xe nào đứng trước mặt biển tam giác viền đỏ MŨI CHÚC XUỐNG DƯỚI -> XE ĐÓ ĐANG Ở ĐƯỜNG PHỤ, BẮT BUỘC PHẢI DỪNG LẠI NHƯỜNG ĐƯỜNG CHO TẤT CẢ CÁC XE KHÁC!"),
            ("Mẹo Ngã tư đồng cấp (Bên phải không vướng)", "Ngã tư không có đèn, không có biển: Xét xe nào mà bên tay phải hoàn toàn trống (không có xe nào) -> Xe đó đi trước. Sau khi xe đó đi, bên phải của xe tiếp theo được giải phóng, cứ thế đi theo chiều kim đồng hồ.")
        ]
    },
    'tiktok_viral': {
        'title': '🔥 15. Bí Kíp Mẹo TikTok Triệu View (Khẩu Quyết Nhìn Phát Chọn Luôn)',
        'items': [
            ("Mẹo Tốc Độ: '10 Đôi - 9 Chiều'", "• ĐƯỜNG ĐÔI: Lấy 10 trừ đi số đầu tốc độ -> Ra đáp án!\n  + 90 km/h: 10 - 9 = 1 -> Chọn Ý 1.\n  + 80 km/h: 10 - 8 = 2 -> Chọn Ý 2.\n  + 70 km/h: 10 - 7 = 3 -> Chọn Ý 3.\n• ĐƯỜNG 2 CHIỀU: Lấy 9 trừ đi số đầu tốc độ -> Ra đáp án!\n  + 80 km/h: 9 - 8 = 1 -> Chọn Ý 1.\n  + 70 km/h: 9 - 7 = 2 -> Chọn Ý 2.\n  + 60 km/h: 9 - 6 = 3 -> Chọn Ý 3.\n  + 50 km/h: 9 - 5 = 4 -> Chọn Ý 4."),
            ("Mẹo CSGT giơ tay", "• CSGT giơ 1 TAY LÊN TRỜI -> Chọn ngay Ý 3 (hoặc nhớ: giơ 1 tay chọn 3, dang 2 tay chọn 1).\n• Khi CSGT giơ tay: Tất cả xe trước/sau/trái/phải phải tuân thủ nghiêm ngặt."),
            ("Mẹo Khái Niệm: '1 Dài, 2 Ngắn'", "• Câu hỏi có: 'Phương tiện thô sơ', 'Người lái xe', 'Khổ giới hạn' -> Chọn ngay Ý 1.\n• Câu hỏi có: 'Làn đường', 'Phương tiện cơ giới', 'Dừng xe', 'Đỗ xe', 'Người điều khiển giao thông' -> Chọn ngay Ý 2."),
            ("Mẹo Sa Hình: Đua xe / Đếm bánh xe", "Gặp câu hỏi các xe đang chạy cùng chiều (đua xe): Nhìn xe đi cuối cùng trong hàng, lấy số bánh trừ đi 1 = Đáp án!\n• Xe ô tô con cuối cùng (4 bánh): 4 - 1 = 3 -> Chọn Ý 3.\n• Xe mô tô cuối cùng (2 bánh): 2 - 1 = 1 -> Chọn Ý 1."),
            ("Mẹo Sa Hình: Xe Chữa Cháy & Quân Sự", "Thấy xe Chữa Cháy hoặc Quân Sự xuất hiện trong sa hình -> Cứ tự tin chọn ngay Ý 2 (100% trúng)!"),
            ("Mẹo Sa Hình: Xe Kéo Xe / Kéo Rơ-moóc", "Thấy hình xe tải kéo rơ-moóc hoặc xe con kéo xe khác -> Nhìn đáp án chọn ngay câu có chữ 'Không đúng' hoặc 'Vi phạm quy tắc giao thông'!"),
            ("Mẹo Biển Tròn Xanh Hiệu Lệnh", "Câu hỏi có 2 hoặc 3 biển tròn màu xanh:\n• Đề bài ngắn (chỉ 1 dòng chữ): Chọn Ý 1.\n• Đề bài dài (từ 2 dòng chữ trở lên): Chọn Ý 3."),
            ("Mẹo Nghiệp Vụ Vận Tải: 'Thuê 1 - Kinh 2'", "• Câu hỏi bắt đầu bằng: 'Người thuê vận tải...', 'Hành khách...' -> Chọn Ý 1.\n• Câu hỏi bắt đầu bằng: 'Người kinh doanh vận tải...' -> Chọn Ý 2.")
        ]
    }
}

# Backward compatibility alias
EXAM_TIPS_CATEGORIES['keyword'] = EXAM_TIPS_CATEGORIES['keywords']
EXAM_TIPS_CATEGORIES['truck_c1'] = EXAM_TIPS_CATEGORIES['mechanic']

# ================= 4. PHÂN BỔ CÁC PHẦN ÔN LUYỆN CHUẨN CỤC ĐƯỜNG BỘ & QUẢN LÝ PHIÊN =================
SECTIONS_CONFIG = {
    'CRITICAL': {
        'id': 'CRITICAL',
        'code': 'crit',
        'name': '⚠️ 60 Câu Điểm Liệt',
        'full_name': '⚠️ 60 Câu Điểm Liệt (Chuẩn Cục Đường Bộ - Cấm Sai Tuyệt Đối)',
        'badge': '⚠️ CÂU ĐIỂM LIỆT (BẮT BUỘC ĐÚNG 100%)',
        'total': 60,
        'filter': lambda q: bool(q.get('isCritical'))
    },
    'CH1': {
        'id': 'CH1',
        'code': 'ch1',
        'name': '📘 Chương 1: Quy tắc giao thông',
        'full_name': '📘 Chương 1: Quy định chung và quy tắc giao thông đường bộ (180 câu)',
        'badge': '📘 Chương 1: Quy tắc giao thông đường bộ',
        'total': 180,
        'filter': lambda q: q.get('chapter') == 1
    },
    'CH2': {
        'id': 'CH2',
        'code': 'ch2',
        'name': '🤝 Chương 2: Văn hóa, Đạo đức & PCCC',
        'full_name': '🤝 Chương 2: Văn hóa giao thông, đạo đức người lái xe, PCCC & Cứu nạn (25 câu)',
        'badge': '🤝 Chương 2: Văn hóa & Đạo đức người lái xe',
        'total': 25,
        'filter': lambda q: q.get('chapter') == 2
    },
    'CH3': {
        'id': 'CH3',
        'code': 'ch3',
        'name': '⚙️ Chương 3: Kỹ thuật lái xe',
        'full_name': '⚙️ Chương 3: Kỹ thuật lái xe ô tô an toàn (58 câu)',
        'badge': '⚙️ Chương 3: Kỹ thuật lái xe ô tô',
        'total': 58,
        'filter': lambda q: q.get('chapter') == 3
    },
    'CH4': {
        'id': 'CH4',
        'code': 'ch4',
        'name': '🔧 Chương 4: Cấu tạo & Sửa chữa',
        'full_name': '🔧 Chương 4: Cấu tạo và sửa chữa xe ô tô thông thường (37 câu)',
        'badge': '🔧 Chương 4: Cấu tạo & Sửa chữa ô tô',
        'total': 37,
        'filter': lambda q: q.get('chapter') == 4
    },
    'CH5': {
        'id': 'CH5',
        'code': 'ch5',
        'name': '🛑 Chương 5: Hệ thống biển báo',
        'full_name': '🛑 Chương 5: Báo hiệu đường bộ (185 câu - 100% Ảnh Gốc Thi Thật)',
        'badge': '🛑 Chương 5: Hệ thống biển báo hiệu đường bộ',
        'total': 185,
        'filter': lambda q: q.get('chapter') == 5
    },
    'CH6': {
        'id': 'CH6',
        'code': 'ch6',
        'name': '🧩 Chương 6: Thế sa hình & Đèn tín hiệu',
        'full_name': '🧩 Chương 6: Giải thế sa hình & Tình huống giao thông (115 câu - 100% Ảnh Gốc Thi Thật)',
        'badge': '🧩 Chương 6: Giải các thế sa hình giao thông',
        'total': 115,
        'filter': lambda q: q.get('chapter') == 6
    }
}

PRACTICE_SESSIONS = {}

def get_section_questions(part_key):
    """Lấy danh sách câu hỏi chuẩn xác tuyệt đối cho từng phần (sorted theo ID)"""
    global ALL_QUESTIONS
    if not ALL_QUESTIONS and os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                ALL_QUESTIONS = json.load(f)
        except Exception as e:
            print(f"[Exam Engine] Error reloading questions.json: {e}")

    cfg = SECTIONS_CONFIG.get(part_key.upper())
    if not cfg:
        for k, v in SECTIONS_CONFIG.items():
            if v['code'] == part_key.lower() or k.lower() == part_key.lower():
                cfg = v
                break
    if not cfg:
        return []
    qs = [q for q in ALL_QUESTIONS if cfg['filter'](q)]
    return sorted(qs, key=lambda x: x.get('id', 0))

def start_practice_session(chat_id, part_key, index=0):
    """Khởi tạo phiên ôn luyện câu hỏi chuẩn xác từng phần"""
    normalized_key = 'CRITICAL'
    for k, v in SECTIONS_CONFIG.items():
        if k.lower() == part_key.lower() or v['code'] == part_key.lower():
            normalized_key = k
            break
            
    qs = get_section_questions(normalized_key)
    session = {
        'chat_id': chat_id,
        'part_key': normalized_key,
        'config': SECTIONS_CONFIG[normalized_key],
        'questions': qs,
        'total': len(qs),
        'current_index': max(0, min(index, len(qs) - 1)) if qs else 0,
        'answers': {},
        'updated_at': time.time()
    }
    PRACTICE_SESSIONS[chat_id] = session
    return session

def get_practice_session(chat_id):
    return PRACTICE_SESSIONS.get(chat_id)

def navigate_practice_question(chat_id, direction='next'):
    """Điều hướng câu hỏi: 'next', 'prev', 'random', hoặc số index cụ thể"""
    session = PRACTICE_SESSIONS.get(chat_id)
    if not session or not session.get('questions'):
        return None, 0, 0, None
    total = session['total']
    curr = session['current_index']
    
    if direction == 'next':
        next_idx = (curr + 1) if curr < total - 1 else 0
    elif direction == 'prev':
        next_idx = (curr - 1) if curr > 0 else (total - 1)
    elif direction == 'random':
        next_idx = random.randint(0, total - 1) if total > 1 else 0
    elif isinstance(direction, int):
        next_idx = max(0, min(direction, total - 1))
    else:
        next_idx = curr
        
    session['current_index'] = next_idx
    session['updated_at'] = time.time()
    return session['questions'][next_idx], next_idx, total, session['config']

