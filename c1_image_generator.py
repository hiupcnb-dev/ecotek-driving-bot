# -*- coding: utf-8 -*-
"""
BỘ SINH HÌNH ẢNH MINH HỌA TRỰC QUAN ĐỒ HỌA CAO CẤP
CHO 600 CÂU HỎI LÝ THUYẾT LÁI XE & BẰNG C1 / B2 / C
Quy chuẩn QCVN 41:2019/BGTVT & Tổng cục Đường bộ Việt Nam
Hỗ trợ đầy đủ:
- Toàn bộ Biển Báo Giao Thông (Chương 6): Biển cấm, Biển nguy hiểm, Biển hiệu lệnh, Biển chỉ dẫn, Vạch kẻ đường
- Toàn bộ Thế Sa Hình (Chương 7): Ngã tư, Cột đèn tín hiệu (Đỏ/Vàng/Xanh), Xe ưu tiên (Hỏa, Công An, Thương), Xe con, Tải, Khách, Mô tô, Mũi tên hướng đi
- Toàn bộ 60 Câu Điểm Liệt: Tình huống nguy hiểm (đường sắt 5m, dốc xe, cao tốc, nồng độ cồn)
"""

import os
import io
import sys
import math
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def get_font(size=16, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahomabd.ttf" if bold else r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = (text or '').strip().split(' ')
    lines = []
    cur_line = ""
    for w in words:
        test_line = (cur_line + " " + w).strip() if cur_line else w
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            cur_line = test_line
        else:
            if cur_line:
                lines.append(cur_line)
            cur_line = w
    if cur_line:
        lines.append(cur_line)
    return lines

# ================= 1. HÀM VẼ CỘT ĐÈN TÍN HIỆU GIAO THÔNG =================
def draw_traffic_light(draw, x, y, active='red', has_arrow=False, arrow_dir='right'):
    """Vẽ cột đèn tín hiệu giao thông 3 màu với quầng sáng glow"""
    bw, bh = 22, 60
    # Thân hộp đèn
    draw.rectangle([x - bw//2, y - bh//2, x + bw//2, y + bh//2], fill="#020617", outline="#94a3b8", width=2)
    # Cột đỡ
    draw.rectangle([x - 2, y + bh//2, x + 2, y + bh//2 + 25], fill="#64748b")
    
    # Đèn Đỏ
    red_col = "#ef4444" if active == 'red' else "#450a0a"
    draw.ellipse([x - 7, y - 24, x + 7, y - 10], fill=red_col)
    if active == 'red':
        draw.ellipse([x - 10, y - 27, x + 10, y - 7], outline="#f87171", width=1)
        
    # Đèn Vàng
    yel_col = "#f59e0b" if active == 'yellow' else "#451a03"
    draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=yel_col)
    if active == 'yellow':
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], outline="#fde047", width=1)

    # Đèn Xanh
    grn_col = "#10b981" if active == 'green' else "#064e3b"
    draw.ellipse([x - 7, y + 10, x + 7, y + 24], fill=grn_col)
    if active == 'green':
        draw.ellipse([x - 10, y + 7, x + 10, y + 27], outline="#34d399", width=1)
        if has_arrow:
            # Mũi tên xanh rẽ phải phụ
            draw.polygon([(x + 2, y + 17), (x - 3, y + 13), (x - 3, y + 21)], fill="#ffffff")

# ================= 2. HÀM VẼ CÁC LOẠI PHƯƠNG TIỆN (TOP-VIEW) =================
def draw_car_top(draw, cx, cy, angle=0, color="#38bdf8", label="CON"):
    """Vẽ xe ô tô con nhìn từ trên xuống (top-view)"""
    w, h = 26, 44
    draw.rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], fill=color, outline="#ffffff", width=2)
    # Kính lái & Kính sau
    draw.rectangle([cx - w//2 + 3, cy - h//2 + 7, cx + w//2 - 3, cy - h//2 + 15], fill="#0f172a")
    draw.rectangle([cx - w//2 + 3, cy + h//2 - 14, cx + w//2 - 3, cy + h//2 - 7], fill="#0f172a")
    # Đèn pha trước
    draw.rectangle([cx - w//2 + 2, cy - h//2, cx - w//2 + 6, cy - h//2 + 3], fill="#facc15")
    draw.rectangle([cx + w//2 - 6, cy - h//2, cx + w//2 - 2, cy - h//2 + 3], fill="#facc15")
    if label:
        draw.text((cx - 12, cy - 6), label, fill="#ffffff", font=get_font(10, bold=True))

def draw_truck_top(draw, cx, cy, angle=0, color="#f97316", label="TẢI"):
    """Vẽ xe tải nhìn từ trên xuống"""
    w, h = 30, 56
    # Thùng xe
    draw.rectangle([cx - w//2, cy - h//2 + 18, cx + w//2, cy + h//2], fill=color, outline="#ffffff", width=2)
    # Đầu cabin
    draw.rectangle([cx - w//2 + 2, cy - h//2, cx + w//2 - 2, cy - h//2 + 16], fill="#1e293b", outline="#ffffff", width=2)
    # Kính lái cabin
    draw.rectangle([cx - w//2 + 5, cy - h//2 + 4, cx + w//2 - 5, cy - h//2 + 10], fill="#38bdf8")
    if label:
        draw.text((cx - 10, cy + 2), label, fill="#ffffff", font=get_font(10, bold=True))

def draw_bus_top(draw, cx, cy, color="#eab308", label="KHÁCH"):
    """Vẽ xe ô tô khách thân dài"""
    w, h = 30, 64
    draw.rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], fill=color, outline="#ffffff", width=2)
    # Dãy cửa kính 2 bên
    for dy in range(-h//2 + 10, h//2 - 10, 10):
        draw.rectangle([cx - w//2 + 2, dy, cx - w//2 + 5, dy + 6], fill="#0f172a")
        draw.rectangle([cx + w//2 - 5, dy, cx + w//2 - 2, dy + 6], fill="#0f172a")
    if label:
        draw.text((cx - 14, cy - 6), label, fill="#0f172a", font=get_font(9, bold=True))

def draw_fire_truck_top(draw, cx, cy):
    """Vẽ xe chữa cháy màu đỏ rực (Ưu tiên 1)"""
    w, h = 32, 60
    draw.rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], fill="#dc2626", outline="#ffffff", width=2)
    # Thang cứu hỏa trên nóc
    draw.rectangle([cx - 5, cy - h//2 + 12, cx + 5, cy + h//2 - 8], fill="#f8fafc", outline="#94a3b8")
    for sy in range(cy - h//2 + 16, cy + h//2 - 8, 8):
        draw.line([(cx - 5, sy), (cx + 5, sy)], fill="#94a3b8", width=1)
    # Đèn ưu tiên chớp xanh
    draw.ellipse([cx - 4, cy - h//2 + 4, cx + 4, cy - h//2 + 12], fill="#38bdf8")
    draw.text((cx - 14, cy - 5), "HỎA", fill="#ffffff", font=get_font(10, bold=True))

def draw_police_car_top(draw, cx, cy):
    """Vẽ xe cảnh sát / công an (Ưu tiên 2)"""
    w, h = 26, 46
    draw.rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], fill="#1d4ed8", outline="#ffffff", width=2)
    # Nóc xe trắng
    draw.rectangle([cx - w//2 + 4, cy - 8, cx + w//2 - 4, cy + 10], fill="#ffffff")
    # Đèn chớp xanh đỏ
    draw.rectangle([cx - 7, cy - 5, cx - 1, cy - 1], fill="#ef4444")
    draw.rectangle([cx + 1, cy - 5, cx + 7, cy - 1], fill="#3b82f6")
    draw.text((cx - 12, cy + 1), "C.AN", fill="#0f172a", font=get_font(9, bold=True))

def draw_ambulance_top(draw, cx, cy):
    """Vẽ xe cứu thương chữ thập đỏ (Ưu tiên 3)"""
    w, h = 28, 50
    draw.rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], fill="#f8fafc", outline="#dc2626", width=2)
    # Chữ thập đỏ trên nóc
    draw.rectangle([cx - 8, cy - 2, cx + 8, cy + 4], fill="#dc2626")
    draw.rectangle([cx - 3, cy - 7, cx + 3, cy + 9], fill="#dc2626")
    # Đèn chớp đỏ
    draw.ellipse([cx - 4, cy - h//2 + 4, cx + 4, cy - h//2 + 10], fill="#dc2626")

def draw_motorcycle_top(draw, cx, cy, label="MÔTÔ"):
    """Vẽ xe mô tô hai bánh"""
    draw.rectangle([cx - 5, cy - 16, cx + 5, cy + 16], fill="#10b981", outline="#ffffff", width=1)
    draw.ellipse([cx - 3, cy - 20, cx + 3, cy - 14], fill="#0f172a") # Bánh trước
    draw.ellipse([cx - 3, cy + 14, cx + 3, cy + 20], fill="#0f172a") # Bánh sau
    draw.line([(cx - 9, cy - 10), (cx + 9, cy - 10)], fill="#ffffff", width=2) # Tay lái
    if label:
        draw.text((cx + 8, cy - 6), label, fill="#10b981", font=get_font(9, bold=True))

# ================= 3. HÀM VẼ CÁC BIỂN BÁO CHUẨN QCVN 41 =================
def draw_sign_p101(draw, cx, cy, r=45):
    """P.101 Đường cấm (Tròn trắng viền đỏ)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)

def draw_sign_p102(draw, cx, cy, r=45):
    """P.102 Cấm đi ngược chiều (Tròn đỏ gạch ngang trắng)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#dc2626")
    draw.rectangle([cx - int(r*0.65), cy - int(r*0.18), cx + int(r*0.65), cy + int(r*0.18)], fill="#ffffff")

def draw_sign_p103a(draw, cx, cy, r=45):
    """P.103a Cấm xe ô tô con"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    draw.rectangle([cx - 20, cy - 8, cx + 20, cy + 12], fill="#1e293b")
    draw.rectangle([cx - 14, cy - 16, cx + 14, cy - 8], fill="#1e293b")
    draw.ellipse([cx - 16, cy + 10, cx - 8, cy + 18], fill="#0f172a")
    draw.ellipse([cx + 8, cy + 10, cx + 16, cy + 18], fill="#0f172a")

def draw_sign_p104(draw, cx, cy, r=45):
    """P.104 Cấm xe mô tô"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    draw.ellipse([cx - 18, cy + 2, cx - 6, cy + 14], outline="#1e293b", width=3)
    draw.ellipse([cx + 6, cy + 2, cx + 18, cy + 14], outline="#1e293b", width=3)
    draw.line([(cx - 12, cy + 8), (cx + 12, cy + 8)], fill="#1e293b", width=3)
    draw.line([(cx - 4, cy - 8), (cx + 4, cy - 8)], fill="#1e293b", width=3)

def draw_sign_p106a(draw, cx, cy, r=45):
    """P.106a Cấm xe tải"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    draw.rectangle([cx - 24, cy - 10, cx + 6, cy + 10], fill="#1e293b")
    draw.rectangle([cx + 8, cy - 2, cx + 22, cy + 10], fill="#1e293b")
    draw.rectangle([cx + 10, cy - 7, cx + 18, cy - 2], fill="#1e293b")
    draw.ellipse([cx - 18, cy + 8, cx - 8, cy + 18], fill="#0f172a")
    draw.ellipse([cx + 11, cy + 8, cx + 21, cy + 18], fill="#0f172a")

def draw_sign_p123(draw, cx, cy, r=45, direction="left"):
    """P.123 Cấm rẽ trái hoặc phải"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    dx = -1 if direction == "left" else 1
    draw.line([(cx - dx*6, cy + 14), (cx - dx*6, cy - 2)], fill="#1e293b", width=4)
    draw.line([(cx - dx*6, cy - 2), (cx + dx*12, cy - 2)], fill="#1e293b", width=4)
    draw.polygon([(cx + dx*18, cy - 2), (cx + dx*10, cy - 8), (cx + dx*10, cy + 4)], fill="#1e293b")
    draw.line([(cx - int(r*0.65), cy - int(r*0.65)), (cx + int(r*0.65), cy + int(r*0.65))], fill="#dc2626", width=6)

def draw_sign_p124(draw, cx, cy, r=45):
    """P.124a Cấm quay đầu xe"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    draw.arc([cx - 16, cy - 16, cx + 16, cy + 12], start=180, end=360, fill="#1e293b", width=4)
    draw.line([(cx + 16, cy - 2), (cx + 16, cy + 14)], fill="#1e293b", width=4)
    draw.line([(cx - 16, cy - 2), (cx - 16, cy + 14)], fill="#1e293b", width=4)
    draw.polygon([(cx - 16, cy + 18), (cx - 22, cy + 10), (cx - 10, cy + 10)], fill="#1e293b")
    draw.line([(cx - int(r*0.65), cy - int(r*0.65)), (cx + int(r*0.65), cy + int(r*0.65))], fill="#dc2626", width=6)

def draw_sign_p125(draw, cx, cy, r=45):
    """P.125 Cấm vượt (Xe đỏ vượt xe đen)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#ffffff", outline="#dc2626", width=8)
    draw.rectangle([cx + 2, cy - 9, cx + 24, cy + 8], fill="#1e293b")
    draw.rectangle([cx - 24, cy - 14, cx - 2, cy + 3], fill="#dc2626")

def draw_sign_p130(draw, cx, cy, r=45):
    """P.130 Cấm dừng và đỗ xe (Chữ X đỏ nền xanh)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#0284c7", outline="#dc2626", width=8)
    d = int(r * 0.68)
    draw.line([(cx - d, cy - d), (cx + d, cy + d)], fill="#dc2626", width=8)
    draw.line([(cx - d, cy + d), (cx + d, cy - d)], fill="#dc2626", width=8)

def draw_sign_p131(draw, cx, cy, r=45):
    """P.131a Cấm đỗ xe (1 gạch chéo đỏ)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#0284c7", outline="#dc2626", width=8)
    d = int(r * 0.68)
    draw.line([(cx - d, cy - d), (cx + d, cy + d)], fill="#dc2626", width=8)

def draw_sign_w205(draw, cx, cy, r=50):
    """W.205 Giao nhau đường cùng cấp (Tam giác vàng viền đỏ, chữ thập đen)"""
    p1 = (cx, cy - r)
    p2 = (cx - int(r * 0.866), cy + int(r * 0.5))
    p3 = (cx + int(r * 0.866), cy + int(r * 0.5))
    draw.polygon([p1, p2, p3], fill="#eab308", outline="#dc2626", width=8)
    draw.line([(cx - 16, cy + 4), (cx + 16, cy + 4)], fill="#1e293b", width=6)
    draw.line([(cx, cy - 12), (cx, cy + 20)], fill="#1e293b", width=6)

def draw_sign_w207(draw, cx, cy, r=50):
    """W.207a Giao nhau với đường không ưu tiên"""
    p1 = (cx, cy - r)
    p2 = (cx - int(r * 0.866), cy + int(r * 0.5))
    p3 = (cx + int(r * 0.866), cy + int(r * 0.5))
    draw.polygon([p1, p2, p3], fill="#eab308", outline="#dc2626", width=8)
    draw.rectangle([cx - 6, cy - 16, cx + 6, cy + 22], fill="#1e293b")
    draw.polygon([(cx, cy - 28), (cx - 14, cy - 14), (cx + 14, cy - 14)], fill="#1e293b")
    draw.rectangle([cx - 24, cy + 6, cx + 24, cy + 12], fill="#1e293b")

def draw_sign_w208(draw, cx, cy, r=50):
    """W.208 Giao nhau với đường ưu tiên (Tam giác ngược đỉnh chúc xuống)"""
    p1 = (cx, cy + r)
    p2 = (cx - int(r * 0.866), cy - int(r * 0.5))
    p3 = (cx + int(r * 0.866), cy - int(r * 0.5))
    draw.polygon([p1, p2, p3], fill="#eab308", outline="#dc2626", width=8)

def draw_sign_w209(draw, cx, cy, r=50):
    """W.209 Giao nhau có tín hiệu đèn"""
    p1 = (cx, cy - r)
    p2 = (cx - int(r * 0.866), cy + int(r * 0.5))
    p3 = (cx + int(r * 0.866), cy + int(r * 0.5))
    draw.polygon([p1, p2, p3], fill="#eab308", outline="#dc2626", width=8)
    draw.rectangle([cx - 7, cy - 16, cx + 7, cy + 20], fill="#1e293b")
    draw.ellipse([cx - 5, cy - 14, cx + 5, cy - 4], fill="#dc2626")
    draw.ellipse([cx - 5, cy - 2, cx + 5, cy + 8], fill="#f59e0b")
    draw.ellipse([cx - 5, cy + 10, cx + 5, cy + 18], fill="#10b981")

def draw_sign_w210(draw, cx, cy, r=50):
    """W.210 Giao nhau với đường sắt có rào chắn"""
    p1 = (cx, cy - r)
    p2 = (cx - int(r * 0.866), cy + int(r * 0.5))
    p3 = (cx + int(r * 0.866), cy + int(r * 0.5))
    draw.polygon([p1, p2, p3], fill="#eab308", outline="#dc2626", width=8)
    draw.line([(cx - 22, cy + 12), (cx + 22, cy + 12)], fill="#1e293b", width=3)
    draw.line([(cx - 18, cy + 2), (cx + 18, cy + 2)], fill="#1e293b", width=3)
    for rx in [-15, -5, 5, 15]:
        draw.line([(cx + rx, cy - 4), (cx + rx, cy + 18)], fill="#1e293b", width=2)

def draw_sign_i401(draw, cx, cy, r=45):
    """I.401 Bắt đầu đường ưu tiên (Hình thoi viền trắng nền vàng)"""
    draw.polygon([(cx, cy - r - 3), (cx + r + 3, cy), (cx, cy + r + 3), (cx - r - 3, cy)], fill="#64748b")
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill="#ffffff")
    inn = int(r * 0.72)
    draw.polygon([(cx, cy - inn), (cx + inn, cy), (cx, cy + inn), (cx - inn, cy)], fill="#eab308")

def draw_sign_r303(draw, cx, cy, r=45):
    """R.303 Vòng xuyến (Tròn xanh 3 mũi tên trắng xoay vòng)"""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#0284c7")
    for deg in [0, 120, 240]:
        rad = math.radians(deg)
        ax = cx + int(20 * math.cos(rad))
        ay = cy + int(20 * math.sin(rad))
        draw.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill="#ffffff")
    draw.arc([cx - 20, cy - 20, cx + 20, cy + 20], start=0, end=360, fill="#ffffff", width=2)

def draw_sign_i409(draw, cx, cy, r=45):
    """I.409 Chỗ quay xe (Vuông xanh mũi tên quay đầu trắng)"""
    draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill="#0284c7", outline="#ffffff", width=3)
    draw.arc([cx - 14, cy - 14, cx + 14, cy + 10], start=180, end=360, fill="#ffffff", width=4)
    draw.line([(cx + 14, cy - 2), (cx + 14, cy + 14)], fill="#ffffff", width=4)
    draw.line([(cx - 14, cy - 2), (cx - 14, cy + 14)], fill="#ffffff", width=4)
    draw.polygon([(cx - 14, cy + 18), (cx - 20, cy + 10), (cx - 8, cy + 10)], fill="#ffffff")

# ================= 4. BỘ VẼ SCENE CHƯƠNG 6: BIỂN BÁO & VẠCH KẺ ĐƯỜNG =================
def draw_signs_scene(draw, q_obj, W, img_y, img_h):
    """Vẽ minh họa chuyên sâu cho các câu hỏi Chương 6 (Biển báo & Vạch kẻ đường)"""
    qid = q_obj.get('id', 0)
    q_txt = q_obj.get('question', '').lower()
    cx = W // 2
    cy = img_y + img_h // 2
    
    font_badge = get_font(15, bold=True)
    font_desc = get_font(13, bold=False)

    # 1. Câu hỏi về Vạch kẻ đường (Vạch liền, vạch đứt, vạch vàng, vạch mắt võng, quả trám, xương cá)
    if any(k in q_txt for k in ['vạch kẻ đường', 'vạch mắt võng', 'vạch xương cá', 'quả trám', 'vạch màu vàng', 'vạch nét liền', 'vạch nét đứt']):
        # Vẽ đoạn đường nhựa
        draw.rectangle([(60, cy - 65), (W - 60, cy + 65)], fill="#334155")
        
        if 'mắt võng' in q_txt:
            # Vạch mắt võng đan chéo vàng
            for offset in range(120, W - 120, 30):
                draw.line([(offset, cy - 60), (offset + 60, cy + 60)], fill="#facc15", width=3)
                draw.line([(offset + 60, cy - 60), (offset, cy + 60)], fill="#facc15", width=3)
            draw.text((80, img_y + 12), "🛣️ VẠCH MẮT VÕNG: CẤM DỪNG ĐỖ XE TRONG VÙNG NÀY ĐỂ CHỐNG ÙN TẮC", fill="#facc15", font=font_badge)

        elif 'quả trám' in q_txt:
            # Vạch hình thoi quả trám
            for rx in [cx - 150, cx, cx + 150]:
                draw.polygon([(rx, cy - 35), (rx + 25, cy), (rx, cy + 35), (rx - 25, cy)], fill="#ffffff")
            draw.text((80, img_y + 12), "🛣️ VẠCH HÌNH THOI QUẢ TRÁM: BÁO SẮP ĐẾN CHỖ NGƯỜI ĐI BỘ QUA ĐƯỜNG", fill="#38bdf8", font=font_badge)

        elif 'xương cá' in q_txt:
            # Vạch xương cá (kênh hóa dòng xe)
            draw.polygon([(cx - 120, cy + 40), (cx + 120, cy + 40), (cx, cy - 40)], fill="#1e293b", outline="#ffffff", width=3)
            for y_line in range(cy - 20, cy + 35, 12):
                draw.line([(cx - 40, y_line), (cx + 40, y_line)], fill="#ffffff", width=3)
            draw.text((80, img_y + 12), "🛣️ VẠCH XƯƠNG CÁ: ĐẢO GIAO THÔNG KÊNH HÓA DÒNG XE - TUYỆT ĐỐI CẤM ĐÈ VẠCH", fill="#f87171", font=font_badge)

        elif 'vàng' in q_txt:
            # Vạch vàng tim đường (phân chia 2 chiều ngược nhau)
            if 'liền' in q_txt:
                draw.line([(60, cy), (W - 60, cy)], fill="#facc15", width=6)
                draw.text((80, img_y + 12), "🛣️ VẠCH VÀNG NÉT LIỀN: ĐƯỜNG 2 CHIỀU - CẤM ĐÈ VẠCH, CẤM LẤN LÀN", fill="#facc15", font=font_badge)
            else:
                for x in range(70, W - 70, 40):
                    draw.line([(x, cy), (x + 20, cy)], fill="#facc15", width=5)
                draw.text((80, img_y + 12), "🛣️ VẠCH VÀNG NÉT ĐỨT: ĐƯỜNG 2 CHIỀU - ĐƯỢC PHÉP ĐÈ VẠCH KHI VƯỢT XE", fill="#facc15", font=font_badge)

        else:
            # Vạch trắng làn cùng chiều
            for x in range(70, W - 70, 40):
                draw.line([(x, cy), (x + 20, cy)], fill="#ffffff", width=4)
            draw.text((80, img_y + 12), "🛣️ VẠCH TRẮNG: PHÂN CHIA CÁC LÀN XE CHẠY CÙNG CHIỀU (ĐỨT: ĐƯỢC CHUYỂN LÀN)", fill="#38bdf8", font=font_badge)
        return

    # 2. Nhận diện các câu hỏi hỏi về 2 hoặc 3 Biển báo (Biển 1, Biển 2, Biển 3)
    if any(k in q_txt for k in ['biển 1', 'biển 2', 'biển 3', 'những biển nào', 'biển nào']):
        # Vẽ bộ 3 Biển chuẩn mực
        bx1, bx2, bx3 = 180, 410, 640
        b_y = cy - 15

        if 'ưu tiên' in q_txt:
            draw_sign_w207(draw, bx1, b_y, r=48)
            draw_sign_i401(draw, bx2, b_y, r=42)
            draw_sign_w208(draw, bx3, b_y, r=48)
        elif 'cấm' in q_txt and 'tải' in q_txt:
            draw_sign_p103a(draw, bx1, b_y, r=45)
            draw_sign_p106a(draw, bx2, b_y, r=45)
            draw_sign_p125(draw, bx3, b_y, r=45)
        elif 'rẽ' in q_txt or 'quay đầu' in q_txt:
            draw_sign_p123(draw, bx1, b_y, r=45, direction="left")
            draw_sign_p124(draw, bx2, b_y, r=45)
            draw_sign_i409(draw, bx3, b_y, r=45)
        elif 'dừng' in q_txt or 'đỗ' in q_txt:
            draw_sign_p130(draw, bx1, b_y, r=45)
            draw_sign_p131(draw, bx2, b_y, r=45)
            draw_sign_p102(draw, bx3, b_y, r=45)
        elif 'đường sắt' in q_txt:
            draw_sign_w210(draw, bx1, b_y, r=48)
            draw_sign_w205(draw, bx2, b_y, r=48)
            draw_sign_w208(draw, bx3, b_y, r=48)
        else:
            draw_sign_p102(draw, bx1, b_y, r=45)
            draw_sign_w208(draw, bx2, b_y, r=48)
            draw_sign_i401(draw, bx3, b_y, r=42)

        # Nhãn Biển 1, Biển 2, Biển 3
        for bx, name in [(bx1, "Biển 1"), (bx2, "Biển 2"), (bx3, "Biển 3")]:
            draw.rectangle([(bx - 42, b_y + 60), (bx + 42, b_y + 88)], fill="#0284c7")
            draw.text((bx - 26, b_y + 66), name, fill="#ffffff", font=font_badge)

        draw.text((50, img_y + 12), "🛑 QUAN SÁT CÁC BIỂN BÁO DƯỚI ĐÂY ĐỂ TRẢ LỜI CÂU HỎI:", fill="#f8fafc", font=font_badge)
        return

    # 3. Vẽ biển đơn chi tiết nếu hỏi về mã biển cụ thể (P.102, W.208, I.401, P.130, v.v.)
    draw.rectangle([(cx - 180, cy - 90), (cx + 180, cy + 90)], fill="#0f172a", outline="#38bdf8", width=2)
    by_single = cy - 15

    sign_title = "BIỂN BÁO HIỆU ĐƯỜNG BỘ"
    if 'p.101' in q_txt or 'đường cấm' in q_txt:
        draw_sign_p101(draw, cx, by_single, r=52)
        sign_title = "P.101: ĐƯỜNG CẤM (TẤT CẢ CÁC XE)"
    elif 'p.102' in q_txt or 'ngược chiều' in q_txt:
        draw_sign_p102(draw, cx, by_single, r=52)
        sign_title = "P.102: CẤM ĐI NGƯỢC CHIỀU"
    elif 'p.103' in q_txt or 'cấm xe ô tô con' in q_txt:
        draw_sign_p103a(draw, cx, by_single, r=52)
        sign_title = "P.103a: CẤM XE Ô TÔ CON VÀ CƠ GIỚI"
    elif 'p.104' in q_txt or 'cấm xe mô tô' in q_txt:
        draw_sign_p104(draw, cx, by_single, r=52)
        sign_title = "P.104: CẤM XE MÔ TÔ HAI BÁNH"
    elif 'p.106' in q_txt or 'cấm xe tải' in q_txt:
        draw_sign_p106a(draw, cx, by_single, r=52)
        sign_title = "P.106a: CẤM XE Ô TÔ TẢI"
    elif 'p.123' in q_txt or 'cấm rẽ' in q_txt:
        draw_sign_p123(draw, cx, by_single, r=52)
        sign_title = "P.123: CẤM RẼ (ĐƯỢC QUAY ĐẦU XE)"
    elif 'p.124' in q_txt or 'quay đầu' in q_txt:
        draw_sign_p124(draw, cx, by_single, r=52)
        sign_title = "P.124: CẤM QUAY ĐẦU (ĐƯỢC RẼ TRÁI)"
    elif 'p.125' in q_txt or 'cấm vượt' in q_txt:
        draw_sign_p125(draw, cx, by_single, r=52)
        sign_title = "P.125: CẤM XE Ô TÔ VƯỢT NHAU"
    elif 'p.130' in q_txt or 'cấm dừng' in q_txt:
        draw_sign_p130(draw, cx, by_single, r=52)
        sign_title = "P.130: CẤM DỪNG XE VÀ CẤM ĐỖ XE"
    elif 'p.131' in q_txt or 'cấm đỗ' in q_txt:
        draw_sign_p131(draw, cx, by_single, r=52)
        sign_title = "P.131a: CẤM ĐỖ XE (ĐƯỢC DỪNG TẠM THỜI)"
    elif 'w.208' in q_txt or 'giao nhau với đường ưu tiên' in q_txt:
        draw_sign_w208(draw, cx, by_single, r=56)
        sign_title = "W.208: GIAO NHAU VỚI ĐƯỜNG ƯU TIÊN"
    elif 'i.401' in q_txt or 'đường ưu tiên' in q_txt:
        draw_sign_i401(draw, cx, by_single, r=48)
        sign_title = "I.401: BẮT ĐẦU ĐOẠN ĐƯỜNG ƯU TIÊN"
    elif 'w.210' in q_txt or 'đường sắt có rào chắn' in q_txt:
        draw_sign_w210(draw, cx, by_single, r=56)
        sign_title = "W.210: GIAO NHAU VỚI ĐƯỜNG SẮT CÓ RÀO CHẮN"
    elif 'r.303' in q_txt or 'vòng xuyến' in q_txt:
        draw_sign_r303(draw, cx, by_single, r=50)
        sign_title = "R.303: GIAO NHAU CHẠY THEO VÒNG XUYẾN"
    else:
        draw_sign_w207(draw, cx, by_single, r=56)
        sign_title = "W.207a: GIAO NHAU VỚI ĐƯỜNG KHÔNG ƯU TIÊN"

    draw.text((cx - len(sign_title)*4, cy + 58), sign_title, fill="#38bdf8", font=font_badge)

# ================= 5. BỘ VẼ SCENE CHƯƠNG 7: SA HÌNH & ĐÈN TÍN HIỆU & XE =================
def draw_sahin_scene(draw, q_obj, W, img_y, img_h):
    """Vẽ giao lộ sa hình hoàn chỉnh: ngã tư, xe cộ, cột đèn tín hiệu Đỏ/Xanh, mũi tên hướng đi"""
    cx = W // 2
    cy = img_y + img_h // 2
    q_txt = q_obj.get('question', '').lower()
    
    font_badge = get_font(14, bold=True)
    font_dir = get_font(11, bold=True)

    # 1. Mặt đường ngã tư nhựa xám
    road_w = 68
    draw.rectangle([(cx - road_w, img_y + 10), (cx + road_w, img_y + img_h - 10)], fill="#334155") # Nhánh dọc
    draw.rectangle([(60, cy - road_w), (W - 60, cy + road_w)], fill="#334155") # Nhánh ngang

    # Vạch tim đường đứt đoạn vàng
    for y_dash in range(img_y + 15, cy - road_w, 16):
        draw.line([(cx, y_dash), (cx, y_dash + 8)], fill="#facc15", width=2)
    for y_dash in range(cy + road_w, img_y + img_h - 15, 16):
        draw.line([(cx, y_dash), (cx, y_dash + 8)], fill="#facc15", width=2)
    for x_dash in range(65, cx - road_w, 16):
        draw.line([(x_dash, cy), (x_dash + 8, cy)], fill="#facc15", width=2)
    for x_dash in range(cx + road_w, W - 65, 16):
        draw.line([(x_dash, cy), (x_dash + 8, cy)], fill="#facc15", width=2)

    # Vạch dừng xe trắng (Stop lines)
    draw.line([(cx - road_w, cy - road_w), (cx + road_w, cy - road_w)], fill="#ffffff", width=3)
    draw.line([(cx - road_w, cy + road_w), (cx + road_w, cy + road_w)], fill="#ffffff", width=3)
    draw.line([(cx - road_w, cy - road_w), (cx - road_w, cy + road_w)], fill="#ffffff", width=3)
    draw.line([(cx + road_w, cy - road_w), (cx + road_w, cy + road_w)], fill="#ffffff", width=3)

    # Vạch người đi bộ qua đường (Zebra crossings)
    for zy in range(cy - road_w + 5, cy + road_w, 14):
        draw.line([(cx - road_w - 18, zy), (cx - road_w - 4, zy)], fill="#ffffff", width=3)
        draw.line([(cx + road_w + 4, zy), (cx + road_w + 18, zy)], fill="#ffffff", width=3)

    # 2. VẼ CỘT ĐÈN TÍN HIỆU GIAO THÔNG (Nếu câu hỏi đề cập đèn tín hiệu hoặc vi phạm)
    has_light = any(k in q_txt for k in ['đèn', 'tín hiệu', 'đỏ', 'xanh', 'vượt đèn'])
    if has_light:
        # Nhánh dưới đèn Xanh (được đi), Nhánh trên đèn Đỏ (phải dừng)
        draw_traffic_light(draw, cx - road_w - 20, cy + road_w + 15, active='green', has_arrow=True)
        draw_traffic_light(draw, cx + road_w + 20, cy - road_w - 15, active='red')
        draw_traffic_light(draw, cx + road_w + 20, cy + road_w + 15, active='red')
        draw_traffic_light(draw, cx - road_w - 20, cy - road_w - 15, active='green')

    # 3. ĐẶT PHƯƠNG TIỆN & MŨI TÊN THEO BỐI CẢNH CÂU HỎI
    if any(k in q_txt for k in ['chữa cháy', 'hỏa', 'ưu tiên', 'công an', 'cứu thương']):
        # Sa hình xe ưu tiên: Xe Hỏa (dưới lên), Xe Công An (phải sang), Xe Con (trái sang)
        draw_fire_truck_top(draw, cx - 24, cy + road_w + 35)
        # Mũi tên xe Hỏa đi thẳng
        draw.line([(cx - 24, cy + road_w + 5), (cx - 24, cy - 20)], fill="#38bdf8", width=3)
        draw.polygon([(cx - 24, cy - 26), (cx - 28, cy - 18), (cx - 20, cy - 18)], fill="#38bdf8")

        draw_police_car_top(draw, cx + road_w + 40, cy - 24)
        # Mũi tên xe Công An đi thẳng
        draw.line([(cx + road_w + 15, cy - 24), (cx - 15, cy - 24)], fill="#38bdf8", width=3)
        draw.polygon([(cx - 20, cy - 24), (cx - 12, cy - 28), (cx - 12, cy - 20)], fill="#38bdf8")

        draw_car_top(draw, cx - road_w - 40, cy + 24, label="CON")
        draw.line([(cx - road_w - 15, cy + 24), (cx - 5, cy + 24)], fill="#38bdf8", width=2)

    elif any(k in q_txt for k in ['bên phải không vướng', 'ngã tư', 'thứ tự']):
        # Ngã tư cùng cấp: Xe Mô tô, Xe Con, Xe Tải
        draw_motorcycle_top(draw, cx + road_w + 35, cy + 24, label="MÔTÔ")
        draw_car_top(draw, cx - 24, cy - road_w - 35, label="CON")
        draw_truck_top(draw, cx - road_w - 45, cy - 24, label="TẢI")

        # Mũi tên
        draw.line([(cx + road_w + 10, cy + 24), (cx - 15, cy + 24)], fill="#10b981", width=3)
        draw.line([(cx - 24, cy - road_w - 10), (cx - 24, cy + 25)], fill="#f59e0b", width=3)
        draw.line([(cx - road_w - 15, cy - 24), (cx + 15, cy - 24)], fill="#38bdf8", width=3)

    elif any(k in q_txt for k in ['xe tải', 'xe khách', 'xe con']):
        # Sa hình xe tải và xe con thông dụng
        draw_truck_top(draw, cx - 24, cy + road_w + 38, label="TẢI")
        # Mũi tên rẽ phải xe tải
        draw.arc([cx - 30, cy + road_w - 30, cx + 30, cy + road_w + 30], start=270, end=360, fill="#10b981", width=3)
        draw.polygon([(cx + 30, cy + road_w - 2), (cx + 24, cy + road_w - 8), (cx + 36, cy + road_w - 8)], fill="#10b981")

        draw_car_top(draw, cx + road_w + 40, cy - 24, label="CON")
        draw.line([(cx + road_w + 15, cy - 24), (cx - 20, cy - 24)], fill="#38bdf8", width=3)

        draw_bus_top(draw, cx - 24, cy - road_w - 45, label="KHÁCH")

    else:
        # Sa hình mặc định: Xe Con + Xe Tải + Đèn tín hiệu
        draw_car_top(draw, cx - 24, cy + road_w + 35, label="CON")
        draw.line([(cx - 24, cy + road_w + 5), (cx - 24, cy - 20)], fill="#38bdf8", width=3)
        draw_truck_top(draw, cx + road_w + 40, cy - 24, label="TẢI")

    # Biển báo cắm ở góc giao lộ nếu có
    if 'ưu tiên' in q_txt:
        draw_sign_i401(draw, cx - road_w - 25, cy + road_w + 35, r=20)
        draw_sign_w208(draw, cx + road_w + 25, cy - road_w - 35, r=22)

    # 4. Thanh ghi chú Quy tắc xét sa hình ở dưới
    draw.rectangle([(25, img_y + img_h - 28), (W - 25, img_y + img_h - 6)], fill="#0f172a", outline="#0284c7")
    draw.text((35, img_y + img_h - 24), "🧩 5 BƯỚC XÉT SA HÌNH: 1. Nhất chớm • 2. Nhì ưu (Hỏa-Quân-Công-Thương) • 3. Tam đường • 4. Tứ hướng • 5. Ngũ rẽ", fill="#38bdf8", font=font_dir)

# ================= 6. HÀM TẠO THẺ HÌNH ẢNH CÂU HỎI TỔNG THỂ =================
def generate_question_card_image(q_obj):
    """
    Sinh thẻ đồ họa hình ảnh câu hỏi chất lượng cao:
    - Nếu câu hỏi có hình ảnh chính thức (318 câu Biển báo & Sa hình): Nạp và hiển thị 100% ảnh gốc của Cục Đường bộ Việt Nam, sắc nét, đúng chuẩn đi thi thật.
    - 60 Câu Điểm Liệt: Tình huống cảnh báo an toàn sống còn trực quan.
    - Chương 1-4 lý thuyết chữ: Infographic kiến thức trọng tâm bằng lái xe C1.
    """
    qid = q_obj.get('id', 1)
    chapter_num = q_obj.get('chapter', 1)
    chapter_name = q_obj.get('chapterName', 'Lý thuyết lái xe ô tô')
    is_crit = q_obj.get('isCritical', False)
    q_title = q_obj.get('question', '')

    W = 850
    dummy_img = Image.new('RGB', (10, 10))
    dummy_draw = ImageDraw.Draw(dummy_img)

    font_header = get_font(20, bold=True)
    font_q = get_font(18, bold=True)
    font_q_body = get_font(16, bold=False)

    title_lines = wrap_text(q_title, font_q_body, 800, dummy_draw)
    if not title_lines:
        title_lines = [q_title]

    y_after_title = 95 + len(title_lines[:3]) * 26
    img_area_y = max(y_after_title + 10, 150)

    # 1. Kiểm tra ảnh gốc chính thức từ thư mục assets/images
    base_dir = os.path.dirname(os.path.abspath(__file__))
    real_img_path = os.path.join(base_dir, 'driving-theory-app', 'assets', 'images', f'cau_{qid}.webp')
    if not os.path.exists(real_img_path) and q_obj.get('image'):
        real_img_path = os.path.join(base_dir, 'driving-theory-app', q_obj['image'].replace('/', os.sep))

    real_img = None
    if os.path.exists(real_img_path):
        try:
            real_img = Image.open(real_img_path).convert('RGB')
        except Exception as e:
            print(f"[Image Gen] Lỗi nạp ảnh gốc câu {qid}: {e}")

    if real_img:
        # Tự động scale ảnh gốc theo tỷ lệ chuẩn, đặt trong khung nền sáng sắc nét
        max_w = 810
        max_h = 360
        rw, rh = real_img.size
        scale = min(max_w / rw, max_h / rh, 1.0)
        if rw < 600 and scale >= 1.0:
            scale = min(max_w / rw, max_h / rh, 1.4)
        new_w = max(10, int(rw * scale))
        new_h = max(10, int(rh * scale))
        real_img_resized = real_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img_area_h = new_h + 20
    elif is_crit:
        img_area_h = 240
    else:
        img_area_h = 260

    H = img_area_y + img_area_h + 50
    img = Image.new('RGB', (W, H), color='#0f172a')
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    badge_bg = "#dc2626" if is_crit else "#1e3a8a"
    draw.rectangle([(0, 0), (W, 55)], fill=badge_bg)
    header_text = f"⚠️ CÂU ĐIỂM LIỆT (BẮT BUỘC ĐÚNG 100%)" if is_crit else f"🚗 KHÓA SÁT HẠCH HẠNG C1 • CHƯƠNG {chapter_num}: {chapter_name.upper()}"
    draw.text((25, 16), header_text, fill="#ffffff", font=font_header)

    # 2. Câu hỏi Title
    draw.text((25, 68), f"CÂU {qid}:", fill="#38bdf8", font=font_q)
    y_text = 95
    for l in title_lines[:3]:
        draw.text((25, y_text), l, fill="#f8fafc", font=font_q_body)
        y_text += 26

    # 3. Khung hiển thị hình ảnh
    draw.rectangle([(20, img_area_y), (W - 20, img_area_y + img_area_h)], 
                   fill="#ffffff" if real_img else "#1e293b", 
                   outline="#38bdf8" if real_img else "#334155", 
                   width=2)

    if real_img:
        # Căn giữa ảnh gốc 100% chính xác của đề thi
        px = 20 + (W - 40 - new_w) // 2
        py = img_area_y + (img_area_h - new_h) // 2
        img.paste(real_img_resized, (px, py))
    elif is_crit:
        # Câu điểm liệt lý thuyết: Cảnh báo an toàn
        cx = W // 2
        cy = img_area_y + img_area_h // 2
        if any(k in q_title.lower() for k in ['rượu', 'bia', 'cồn', 'ma túy']):
            draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill="#ffffff", outline="#dc2626", width=8)
            draw.line([(cx - 35, cy - 35), (cx + 35, cy + 35)], fill="#dc2626", width=6)
            draw.text((cx - 28, cy - 10), "CỒN = 0", fill="#1e293b", font=get_font(15, bold=True))
            draw.text((cx - 160, cy + 65), "NGHIÊM CẤM TUYỆT ĐỐI NỒNG ĐỘ CỒN VÀ MA TÚY KHI LÁI XE", fill="#ef4444", font=get_font(14, bold=True))
        else:
            draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill="#ffffff", outline="#dc2626", width=8)
            draw.line([(cx - 35, cy - 35), (cx + 35, cy + 35)], fill="#dc2626", width=6)
            draw.text((cx - 24, cy - 10), "CẤM", fill="#1e293b", font=get_font(16, bold=True))
            draw.text((cx - 180, cy + 65), "CÂU ĐIỂM LIỆT: ĐI THI CHỌN SAI CÂU NÀY BỊ TRƯỢT NGAY LẬP TỨC!", fill="#ef4444", font=get_font(14, bold=True))
    else:
        # Infographic chuyên đề xe tải C1 / Lý thuyết chung
        draw.rectangle([(25, img_area_y + 10), (W - 25, img_area_y + img_area_h - 10)], fill="#0f172a")
        draw.text((45, img_area_y + 20), "🚚 CHUYÊN ĐỀ SÁT HẠCH LÝ THUYẾT LÁI XE HẠNG C1", fill="#38bdf8", font=get_font(16, bold=True))
        draw.text((45, img_area_y + 55), "• Khối lượng xe tải C1: Trên 3.500 kg đến 7.500 kg • Kéo rơ moóc ≤ 750 kg", fill="#f8fafc", font=get_font(14, bold=True))
        draw.text((45, img_area_y + 90), "• Phạm vi giấy phép: Được điều khiển toàn bộ các loại xe quy định cho GPLX hạng B", fill="#38bdf8", font=get_font(14, bold=True))
        draw.text((45, img_area_y + 125), "• Độ tuổi tối thiểu: Đủ 21 tuổi trở lên • Lái liên tục ≤ 4 giờ, trong ngày ≤ 10 giờ", fill="#94a3b8", font=get_font(14, bold=True))
        draw.text((45, img_area_y + 160), "• Hệ thống phanh khí nén (phanh hơi): Kiểm tra áp suất khí, xả nước đáy bình tích", fill="#facc15", font=get_font(14, bold=True))
        draw.text((45, img_area_y + 195), "• Chấp hành hiệu lệnh: Hiệu lệnh CSGT > Đèn tín hiệu > Biển báo > Vạch kẻ đường", fill="#10b981", font=get_font(14, bold=True))

    # 4. Footer hướng dẫn
    draw.rectangle([(20, H - 40), (W - 20, H - 10)], fill="#1e293b", outline="#0284c7", width=1)
    draw.text((35, H - 32), "👉 Chi tiết các đáp án [1], [2], [3] hiển thị đầy đủ bên dưới tin nhắn! Bấm nút để chọn.", fill="#38bdf8", font=get_font(13, bold=True))

    buf = io.BytesIO()
    img.save(buf, format='PNG', quality=95)
    return buf.getvalue()


# ================= 7. HÀM TẠO ẢNH TIẾN ĐỘ VÀ KHÓA HỌC C1 =================
def generate_c1_course_overview_image(status=None):
    if status is None:
        status = {}
    web_time_str = status.get('webOfficialText', '7 giờ 18 phút')
    W, H = 840, 560
    img = Image.new('RGB', (W, H), color='#0f172a')
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 70)], fill="#1e3a8a")
    draw.text((25, 20), "🚗 CHƯƠNG TRÌNH ĐÀO TẠO LÁI XE HẠNG C1 (EcoTek LMS)", fill="#ffffff", font=get_font(22, bold=True))

    draw.rectangle([(20, 85), (W - 20, 160)], fill="#1e293b", outline="#334155", width=2)
    draw.text((35, 95), "👤 Học viên: NGUYỄN TRUNG HIẾU  |  Khóa: K01Đ09 (Hạng C1)", fill="#38bdf8", font=get_font(16, bold=True))
    draw.text((35, 125), f"⏱️ Thời gian tích lũy: {web_time_str}  |  Mục tiêu: 90 giờ  |  Hạn chót: 18/10/2026", fill="#f8fafc", font=get_font(15, bold=False))

    courses = [
        ("Môn 1: Pháp luật giao thông đường bộ", "9h 30m", "100%", "#10b981", "24/24 bài • ĐÃ HOÀN THÀNH"),
        ("Môn 2: Cấu tạo và sửa chữa thông thường", "7h 30m", "Đang học", "#38bdf8", "18 bài • Động cơ Diesel, Phanh khí nén"),
        ("Môn 3: Nghiệp vụ vận tải hàng hóa (C1)", "6h 00m", "Chờ học", "#f59e0b", "16 bài • Tải trọng 3.5t - 7.5t, Xếp dỡ"),
        ("Môn 4: Đạo đức & Văn hóa giao thông", "5h 00m", "Chờ học", "#94a3b8", "14 bài • Trách nhiệm tài xế, Sơ cứu"),
        ("Môn 5: Kỹ thuật lái xe ô tô tải C1", "8h 30m", "Chờ học", "#94a3b8", "20 bài • Đề-pa dốc số sàn, Điểm mù xe tải")
    ]

    y_c = 175
    for name, hrs, prog, col, note in courses:
        draw.rectangle([(20, y_c), (W - 20, y_c + 58)], fill="#1e293b", outline="#334155", width=1)
        draw.ellipse([(35, y_c + 14), (65, y_c + 44)], fill=col)
        draw.text((44, y_c + 18), "✓" if prog == "100%" else "▶", fill="#ffffff", font=get_font(15, bold=True))
        draw.text((80, y_c + 10), name, fill="#ffffff", font=get_font(16, bold=True))
        draw.text((80, y_c + 34), f"Thời lượng: {hrs}  •  {note}", fill="#94a3b8", font=get_font(13, bold=False))
        draw.rectangle([(W - 130, y_c + 14), (W - 35, y_c + 44)], fill=col)
        draw.text((W - 120, y_c + 19), prog, fill="#ffffff", font=get_font(14, bold=True))
        y_c += 68

    draw.rectangle([(20, H - 55), (W - 20, H - 15)], fill="#0f172a", outline="#0284c7", width=1)
    draw.text((35, H - 43), "🤖 Tool EcoTek Auto tự động chạy ngầm & nộp bài trắc nghiệm 100% chuẩn xác!", fill="#38bdf8", font=get_font(14, bold=True))

    buf = io.BytesIO()
    img.save(buf, format='PNG', quality=95)
    return buf.getvalue()

def generate_c1_truck_infographic():
    W, H = 840, 540
    img = Image.new('RGB', (W, H), color='#0f172a')
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 65)], fill="#0369a1")
    draw.text((25, 18), "🚛 CẨM NANG TOÀN DIỆN BẰNG LÁI XE TẢI HẠNG C1", fill="#ffffff", font=get_font(22, bold=True))

    items = [
        ("1. PHẠM VI BẰNG C1 (LUẬT 2024)", "Điều khiển ô tô tải và ô tô chuyên dùng có khối lượng toàn bộ từ 3.500 kg đến 7.500 kg; kéo rơ moóc đến 750 kg và xe hạng B. Độ tuổi tối thiểu: Đủ 21 tuổi trở lên.", "#38bdf8"),
        ("2. HỆ THỐNG PHANH KHÍ NÉN (PHANH HƠI)", "Xe tải C1 sử dụng phanh khí nén 2 dòng. Trước khi chạy phải nổ máy tích đủ áp suất khí (đồng hồ báo vùng xanh). Hàng ngày phải xả nước đọng ở van đáy bình tích khí.", "#f59e0b"),
        ("3. ĐỀ-PA DỐC SỐ SÀN XE TẢI NẶNG", "Quy trình 4 bước: 1. Đạp hết côn + kéo phanh tay; 2. Đệm ga 1.200 - 1.500 rpm; 3. Nhả côn từ từ đến khi đầu xe RUNG NHỔM LÊN; 4. GIỮ NGUYÊN CÔN và hạ phanh tay.", "#10b981"),
        ("4. ĐỔ ĐÈO & XUỐNG DỐC CAO", "Luôn 'Lên dốc số nào - Xuống dốc số đó'. Về số thấp (số 1 hoặc số 2) để hãm động cơ + phanh cúp-pô. TUYỆT ĐỐI KHÔNG đạp hết côn, không về số mo (N), không tắt máy.", "#ef4444"),
        ("5. ĐIỂM MÙ XE TẢI & QUY TẮC AN TOÀN", "Xe tải có 4 vùng điểm mù lớn: Sát đầu xe, sau đuôi xe và sườn bên phải. Khi chuyển làn hoặc vào cua phải quan sát gương sớm và bật xi-nhan trước tối thiểu 30m.", "#c084fc")
    ]

    y_i = 85
    for title, desc, col in items:
        draw.rectangle([(20, y_i), (W - 20, y_i + 80)], fill="#1e293b", outline="#334155", width=1)
        draw.rectangle([(20, y_i), (28, y_i + 80)], fill=col)
        draw.text((40, y_i + 8), title, fill=col, font=get_font(16, bold=True))
        
        words = desc.split(' ')
        lines = []
        cur = ""
        for w in words:
            if len(cur + " " + w) > 72:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
            
        y_d = y_i + 32
        for l in lines[:2]:
            draw.text((40, y_d), l, fill="#e2e8f0", font=get_font(14, bold=False))
            y_d += 20
        y_i += 88

    buf = io.BytesIO()
    img.save(buf, format='PNG', quality=95)
    return buf.getvalue()
