# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH ĐÀO TẠO & SÁT HẠCH LÝ THUYẾT LÁI XE HẠNG C1
Chuẩn Luật Trật tự, an toàn giao thông đường bộ 2024 & Hệ thống EcoTek LMS
"""

# ================= 1. DANH MỤC 5 MÔN HỌC BẮT BUỘC HẠNG C1 =================
C1_COURSES = [
    {
        "id": 1,
        "code": "PLGT",
        "name": "Môn 1: Pháp luật giao thông đường bộ",
        "totalHours": "9 giờ 30 phút",
        "totalLessons": 24,
        "desc": "Quy tắc chung, đường ưu tiên, tốc độ tối đa, khoảng cách an toàn, nồng độ cồn, độ tuổi và giấy phép lái xe C1.",
        "icon": "⚖️",
        "coreTopics": [
            "Độ tuổi lái xe C1: Đủ 21 tuổi trở lên.",
            "Quy định nồng độ cồn: BỊ NGHIÊM CẤM TUYỆT ĐỐI (chỉ số bằng 0).",
            "Tốc độ trong khu đông dân cư: Có dải phân cách giữa: 60 km/h; Không dải phân cách: 50 km/h.",
            "Khoảng cách an toàn tối thiểu: V=60: 35m; 60<V≤80: 55m; 80<V≤100: 70m; 100<V≤120: 100m.",
            "Thời gian làm việc tài xế: Lái xe liên tục không quá 4 giờ; Tổng trong ngày không quá 10 giờ.",
            "Niên hạn sử dụng: Xe ô tô tải (hàng hóa) là 25 năm; Xe chở người trên 9 chỗ là 20 năm."
        ]
    },
    {
        "id": 2,
        "code": "CTSC",
        "name": "Môn 2: Cấu tạo và sửa chữa thông thường",
        "totalHours": "7 giờ 30 phút",
        "totalLessons": 18,
        "desc": "Cấu tạo động cơ Diesel, hộp số sàn, phanh khí nén (phanh hơi), hệ thống treo, lốp tải và bảo dưỡng định kỳ.",
        "icon": "🔧",
        "coreTopics": [
            "Động cơ Diesel: Sử dụng nhiên liệu dầu DO, tự bốc cháy do nhiệt độ và áp suất nén cao (không dùng bugi đánh lửa).",
            "Hệ thống phanh khí nén (Phanh hơi xe tải): Dùng áp lực khí nén để đẩy bầu phanh ép má phanh vào tang trống. Phải kiểm tra đồng hồ áp suất khí và xả nước đọng đáy bình khí nén hàng ngày.",
            "Ly hợp (Côn): Ngắt và truyền mô men xoắn từ động cơ tới hộp số. Khi chuyển số phải đạp hết hành trình chân côn.",
            "Ắc quy ô tô: Tích trữ và cung cấp điện một chiều cho máy khởi động (củ đề) và phụ tải điện.",
            "Lốp xe tải: Chịu toàn bộ tải trọng của xe và hàng hóa. Phải kiểm tra áp suất chuẩn, xiết chặt bu-lông bánh xe, không dùng lốp mòn quá vạch TWI."
        ]
    },
    {
        "id": 3,
        "code": "NVVT",
        "name": "Môn 3: Nghiệp vụ vận tải hàng hóa (Trọng tâm C1)",
        "totalHours": "6 giờ 00 phút",
        "totalLessons": 16,
        "desc": "Quy định tải trọng bằng C1 (3.500kg - 7.500kg), hợp đồng vận chuyển, giấy vận tải, kỹ thuật xếp dỡ và chằng buộc hàng hóa.",
        "icon": "🚛",
        "coreTopics": [
            "Quy định Bằng C1: Điều khiển ô tô tải và ô tô chuyên dùng có khối lượng toàn bộ từ 3.500 kg đến 7.500 kg; kéo rơ moóc đến 750 kg.",
            "Quy cách xếp hàng: Hàng nặng xếp dưới sát sàn thùng xe và giữa tâm xe; hàng nhẹ xếp trên; hàng tròn (ống thép, phuy) phải chèn chặt chống lăn.",
            "Chằng buộc hàng hóa: Dùng dây cáp, dây tăng đơ chằng buộc chắc chắn vào móc hãm của sàn thùng xe; che bạt kín chống rơi vãi.",
            "Chiều cao xếp hàng: Xe tải thùng hở không vượt quá chiều cao quy định ghi trong Giấy chứng nhận đăng kiểm.",
            "Hàng siêu trường, siêu trọng: Là hàng không thể tháo rời; chỉ được lưu hành khi có Giấy phép lưu hành đặc biệt của cơ quan quản lý đường bộ."
        ]
    },
    {
        "id": 4,
        "code": "DDLX",
        "name": "Môn 4: Đạo đức người lái xe & Văn hóa giao thông",
        "totalHours": "5 giờ 00 phút",
        "totalLessons": 14,
        "desc": "Trách nhiệm nghề nghiệp của tài xế tải, phòng chống rượu bia, ứng xử văn minh và sơ cứu nạn nhân tai nạn giao thông.",
        "icon": "❤️",
        "coreTopics": [
            "Trách nhiệm nghề nghiệp: Tuyệt đối chấp hành luật, yêu xe như con, quý hàng như tính mạng.",
            "Ứng xử văn hóa: Nhường đường cho xe ưu tiên, xe nhỏ hơn và người đi bộ; không phóng nhanh giành đường.",
            "Sơ cứu tai nạn: Lập tức dừng xe, bảo vệ hiện trường, ngắt khóa điện chống cháy nổ, báo 115 và cấp cứu người bị nạn.",
            "Sơ cứu gãy xương: Cố định nẹp bất động 2 khớp (khớp trên và khớp dưới ổ gãy); không nắn bóp xương gãy."
        ]
    },
    {
        "id": 5,
        "code": "KTLX",
        "name": "Môn 5: Kỹ thuật lái xe ô tô tải Hạng C1",
        "totalHours": "8 giờ 30 phút",
        "totalLessons": 20,
        "desc": "Thao tác buồng lái số sàn, kỹ thuật chân côn, đề-pa dốc tải trọng lớn, phanh động cơ đổ đèo và căn điểm mù xe tải.",
        "icon": "🎮",
        "coreTopics": [
            "Thao tác buồng lái MT: Chân trái CHỈ ĐẠP CÔN; chân phải phụ trách cả PHANH và GA (thế chữ V).",
            "Đề-pa lên dốc xe tải: Phanh chân + đạp hết côn -> Kéo phanh tay -> Đệm ga lên 1.200 - 1.500 rpm -> Nhả côn từ từ đến khi đầu xe RUNG NHỔM LÊN -> Giữ chân côn và hạ phanh tay.",
            "Xuống dốc cao, dốc dài: VỀ SỐ THẤP (số 1 hoặc số 2), dùng phanh động cơ kết hợp phanh cúp-pô (exhaust brake). TUYỆT ĐỐI KHÔNG cắt côn, không về số mo (N), không tắt máy.",
            "Điểm mù xe tải: Gồm 4 vùng mù nguy hiểm: Ngay sát đầu cabin phía trước, góc gương bên phải (cực rộng), ngay sau đuôi thùng xe và sát sườn xe.",
            "Lùi xe chuồng xe tải: Quan sát kỹ cả hai gương chiếu hậu bản lớn; lùi chậm và điều chỉnh vô lăng sớm hơn xe con do chiều dài cơ sở lớn."
        ]
    }
]

# ================= 2. NGÂN HÀNG BIỂN BÁO GIAO THÔNG QCVN 41 =================
TRAFFIC_SIGNS_LIST = [
    {
        "code": "P.106a",
        "name": "Cấm xe ô tô tải",
        "category": "Biển báo cấm",
        "desc": "Cấm ô tô tải có khối lượng chuyên chở lớn hơn 1.5 tấn (trừ xe ưu tiên).",
        "tip": "Gặp biển này thì xe tải C1 (3.5t - 7.5t) TUYỆT ĐỐI KHÔNG ĐƯỢC ĐI VÀO."
    },
    {
        "code": "P.126",
        "name": "Cấm xe ô tô tải vượt",
        "category": "Biển báo cấm",
        "desc": "Cấm tất cả các loại ô tô tải vượt các xe cơ giới khác. Ô tô con vẫn được phép vượt.",
        "tip": "Biển tròn đỏ vẽ ô tô tải đỏ cạnh ô tô con đen -> Chỉ cấm xe tải vượt."
    },
    {
        "code": "P.115",
        "name": "Hạn chế tải trọng toàn bộ xe",
        "category": "Biển báo cấm",
        "desc": "Cấm các loại xe có tải trọng toàn bộ (xe + hàng) vượt quá trị số ghi trên biển (vd: 10T, 14T).",
        "tip": "Tài xế C1 phải biết chính xác tổng tải trọng xe mình để không phạm luật."
    },
    {
        "code": "P.123a",
        "name": "Cấm rẽ trái",
        "category": "Biển báo cấm",
        "desc": "Cấm các loại xe rẽ trái ở nơi đường giao nhau (Theo Quy chuẩn 41 mới: CẤM RẼ TRÁI KHÔNG CẤM QUAY ĐẦU).",
        "tip": "Rất hay thi: Gặp biển cấm rẽ trái thì vẫn ĐƯỢC PHÉP QUAY ĐẦU XE."
    },
    {
        "code": "P.124a",
        "name": "Cấm quay đầu xe",
        "category": "Biển báo cấm",
        "desc": "Cấm các loại xe quay đầu xe nhưng ĐƯỢC PHÉP RẼ TRÁI.",
        "tip": "Biển chữ U gạch chéo -> Cấm quay đầu nhưng VẪN ĐƯỢC RẼ TRÁI."
    },
    {
        "code": "W.207a",
        "name": "Giao nhau với đường không ưu tiên",
        "category": "Biển báo nguy hiểm",
        "desc": "Tam giác đỉnh hướng lên, vẽ mũi tên lớn có đường nhỏ cắt ngang. Xe trên đường này ĐƯỢC ƯU TIÊN QUA NƠI GIAO NHAU.",
        "tip": "Mũi tên to đi thẳng là đường ưu tiên -> Xe mình được quyền đi trước."
    },
    {
        "code": "W.208",
        "name": "Giao nhau với đường ưu tiên",
        "category": "Biển báo nguy hiểm",
        "desc": "Tam giác ngược đỉnh chúc xuống dưới. Báo trước sắp giao cắt với đường ưu tiên.",
        "tip": "Đỉnh chúc xuống -> Bắt buộc phải NHƯỜNG ĐƯỜNG cho xe trên đường ưu tiên."
    },
    {
        "code": "I.401",
        "name": "Bắt đầu đường ưu tiên",
        "category": "Biển chỉ dẫn",
        "desc": "Hình thoi viền trắng nền vàng. Báo hiệu các phương tiện đi trên đường này được quyền ưu tiên đi trước.",
        "tip": "Hình thoi vàng = ĐƯỜNG ƯU TIÊN -> Được đi trước qua ngã ba ngã tư."
    },
    {
        "code": "I.452",
        "name": "Đường cao tốc",
        "category": "Biển chỉ dẫn",
        "desc": "Hình chữ nhật màu xanh lá cây, vẽ 2 dải đường màu trắng và cầu vượt.",
        "tip": "Quy tắc cao tốc: Không được quay đầu, lùi xe, chạy trên làn dừng khẩn cấp."
    }
]

# ================= 3. THẦN CHÚ GIẢI THẾ SA HÌNH KINH ĐIỂN =================
SA_HINH_RULES = [
    {
        "step": 1,
        "name": "NHẤT CHỚM",
        "rule": "Xe nào đã chớm vào ngã tư trước (đã vượt qua vạch dừng của người đi bộ) thì ĐƯỢC QUYỀN ĐI TRƯỚC NHẤT, kể cả xe ưu tiên cũng phải nhường."
    },
    {
        "step": 2,
        "name": "NHÌ ƯU",
        "rule": "Thứ tự xe ưu tiên chuẩn: HỎA (Cứu hỏa) ➔ QUÂN (Quân sự) ➔ CÔNG (Công an) ➔ THƯƠNG (Cứu thương). Xe Cứu hỏa luôn luôn đi trước xe Công an."
    },
    {
        "step": 3,
        "name": "TAM ĐƯỜNG",
        "rule": "Xe đi trên ĐƯỜNG ƯU TIÊN (có biển hình thoi I.401 hoặc biển tam giác mũi tên to W.207a) được đi trước xe đi trên đường nhánh/đường không ưu tiên (có biển tam giác ngược W.208)."
    },
    {
        "step": 4,
        "name": "TỨ HƯỚNG",
        "rule": "Ngã tư cùng cấp: Xe có BÊN PHẢI KHÔNG BỊ VƯỚNG (bên phải không có xe) được quyền đi đầu tiên."
    },
    {
        "step": 5,
        "name": "HƯỚNG ĐI",
        "rule": "Thứ tự ưu tiên theo hướng rẽ: Xe RẼ PHẢI ➔ Xe ĐI THẲNG ➔ Xe RẼ TRÁI (Xe rẽ trái luôn phải nhường đường cho xe đi thẳng)."
    }
]
