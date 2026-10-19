# -*- coding: utf-8 -*-
"""
CẨM NANG & ENGINE 120 TÌNH HUỐNG MÔ PHỎNG GIAO THÔNG V2.0.0
Quy chuẩn Cục Đường bộ Việt Nam / Tổng cục Đường bộ:
- 120 tình huống chia làm 6 chương
- Thang điểm 5 - 4 - 3 - 2 - 1 - 0 (Đạt: từ 35/50 điểm trở lên)
- Điểm căn vàng bấm phím SPACE bắt trọn 5 điểm
"""

import random
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Dữ liệu 120 tình huống mô phỏng chuẩn xác V2.0.0
SIMULATION_SITUATIONS = {
    # ================= CHƯƠNG 1: ĐÔ THỊ, KHU ĐÔNG DÂN CƯ (1 - 29) =================
    1: {'ch': 1, 'title': 'Người đi bộ khuất sau xe tải sang đường', 'cue': 'Người đi bộ vừa bước chân qua đuôi xe tải', 'group': 'pedestrian'},
    2: {'ch': 1, 'title': 'Người đi bộ vượt dải phân cách sang đường', 'cue': 'Người đi bộ vừa bước chân qua dải phân cách', 'group': 'pedestrian'},
    3: {'ch': 1, 'title': 'Xe con phía trước phanh gấp tránh xe máy', 'cue': 'Đèn phanh xe con phía trước vừa chớm đỏ', 'group': 'brake_light'},
    4: {'ch': 1, 'title': 'Xe con từ đường nhánh rẽ phải vào ngã ba', 'cue': 'Đầu xe con từ đường nhánh vừa chạm mép đường', 'group': 'intersection'},
    5: {'ch': 1, 'title': 'Xe máy rẽ trái tạt đầu xe ô tô của bạn', 'cue': 'Xe máy bắt đầu đánh lái chớm sang làn xe mình', 'group': 'cut_in'},
    6: {'ch': 1, 'title': 'Xe buýt lấn làn vượt xe khác ở chiều đối diện', 'cue': 'Đầu xe buýt ngược chiều vừa lấn qua vạch tim đường', 'group': 'lane_cross'},
    7: {'ch': 1, 'title': 'Xe con phía trước phanh gấp dừng chờ người đi bộ', 'cue': 'Đèn phanh đỏ xe con trước vừa bật sáng', 'group': 'brake_light'},
    8: {'ch': 1, 'title': 'Xe đạp từ ngõ nhỏ bất ngờ lao ra', 'cue': 'Bánh trước xe đạp vừa chạm mép vỉa hè lao xuống đường', 'group': 'pedestrian'},
    9: {'ch': 1, 'title': 'Xe tải phía trước lấn làn vượt xe khác', 'cue': 'Đầu xe tải vừa lấn sang làn đường của bạn', 'group': 'lane_cross'},
    10: {'ch': 1, 'title': 'Xe con từ đường nhánh bên trái nhập vào đường chính', 'cue': 'Đầu xe con bên trái vừa nhô ra khỏi tường rào', 'group': 'intersection'},
    11: {'ch': 1, 'title': 'Xe bồn bê tông từ đường nhánh bên phải lao ra ngã ba', 'cue': 'Đầu xe bồn vừa xuất hiện ngang cột A bên phải', 'group': 'intersection'},
    12: {'ch': 1, 'title': 'Xe máy bất ngờ rẽ trái trước đầu xe con', 'cue': 'Xe máy bắt đầu xi-nhan và bánh xe chạm vạch phân làn', 'group': 'cut_in'},
    13: {'ch': 1, 'title': 'Xe máy chở hàng cồng kềnh ngã ra đường', 'cue': 'Xe máy bắt đầu chao đảo nghiêng đổ', 'group': 'cut_in'},
    14: {'ch': 1, 'title': 'Xe tải đi qua gầm cầu chui khuất tầm nhìn', 'cue': 'Đầu xe tải ngược chiều vừa nhô ra khỏi chân cầu vượt', 'group': 'lane_cross'},
    15: {'ch': 1, 'title': 'Xe con phía trước phanh gấp dừng tránh xe máy', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    16: {'ch': 1, 'title': 'Xe con bên trái rẽ trái tạt đầu xe bạn', 'cue': 'Đầu xe con bên trái đè lên vạch tim đường', 'group': 'cut_in'},
    17: {'ch': 1, 'title': 'Xe buýt mở cửa cho khách xuống sang đường ẩu', 'cue': 'Hành khách vừa bước chân xuống lòng đường', 'group': 'pedestrian'},
    18: {'ch': 1, 'title': 'Tài xế xe đỗ bên đường bất ngờ mở cửa xe', 'cue': 'Cánh cửa xe con màu bạc vừa hé mở khoảng 10cm', 'group': 'car_door'},
    19: {'ch': 1, 'title': 'Xe con đỗ bên phải đường bắt đầu xuất phát', 'cue': 'Bánh trước xe con bên phải vừa đánh lái chồm ra làn đường', 'group': 'cut_in'},
    20: {'ch': 1, 'title': 'Xe máy đỗ bên lề đường bất ngờ quay đầu', 'cue': 'Xe máy vừa quay ngang đầu xe hướng ra giữa đường', 'group': 'cut_in'},
    21: {'ch': 1, 'title': 'Xe con phía trước phanh gấp nhường đường cho xe quay đầu', 'cue': 'Đèn phanh đỏ xe con trước vừa sáng lên', 'group': 'brake_light'},
    22: {'ch': 1, 'title': 'Xe con từ ngã tư không có đèn tín hiệu lao ra', 'cue': 'Đầu xe con vừa nhô qua mép tường ngã tư', 'group': 'intersection'},
    23: {'ch': 1, 'title': 'Xe tải lấn làn vượt xe rác đang dừng', 'cue': 'Đầu xe tải ngược chiều vừa vượt qua thân xe rác', 'group': 'lane_cross'},
    24: {'ch': 1, 'title': 'Xe tải ngược chiều lấn làn tránh đống cát ven đường', 'cue': 'Bánh trước xe tải vừa chạm vào vạch kẻ tim đường', 'group': 'lane_cross'},
    25: {'ch': 1, 'title': 'Xe con đi lùi ra khỏi gara nhà bên phải', 'cue': 'Đuôi xe con vừa nhô ra khỏi cửa gara', 'group': 'intersection'},
    26: {'ch': 1, 'title': 'Xe máy lách qua chướng ngại vật lao sang làn bạn', 'cue': 'Đầu xe máy vừa chớm đè vạch phân cách', 'group': 'cut_in'},
    27: {'ch': 1, 'title': 'Xe cứu thương ưu tiên từ đường nhánh lao vào ngã tư', 'cue': 'Đầu xe cứu thương vừa xuất hiện giữa ngã tư', 'group': 'intersection'},
    28: {'ch': 1, 'title': 'Xe con phía trước phanh gấp vì người đi bộ qua đường', 'cue': 'Đèn phanh đỏ xe con phía trước vừa chớm sáng', 'group': 'brake_light'},
    29: {'ch': 1, 'title': 'Xe máy đi ngược chiều lách trước đầu xe bạn', 'cue': 'Bánh trước xe máy ngược chiều vừa rẽ ngang trước mặt', 'group': 'cut_in'},

    # ================= CHƯƠNG 2: ĐƯỜNG NÔNG THÔN, ĐÈO DỐC (30 - 43) =================
    30: {'ch': 2, 'title': 'Đàn bò bất ngờ đi từ lề đường ra giữa đường', 'cue': 'Con bò đầu tiên vừa bước chân xuống lòng đường', 'group': 'animal'},
    31: {'ch': 2, 'title': 'Đàn bò đứng gặm cỏ tràn ra làn xe chạy', 'cue': 'Con bò quay đầu bước sang mép đường nhựa', 'group': 'animal'},
    32: {'ch': 2, 'title': 'Người đi bộ từ đường bờ ruộng băng qua đường', 'cue': 'Người đi bộ vừa bước chân lên mép mặt đường nhựa', 'group': 'pedestrian'},
    33: {'ch': 2, 'title': 'Trẻ em bất ngờ đuổi theo bóng chạy ra đường', 'cue': 'Đứa bé đầu tiên vừa chạy vụt ra khỏi cổng nhà', 'group': 'pedestrian'},
    34: {'ch': 2, 'title': 'Xe máy chở nông sản cồng kềnh rẽ gấp ở khúc cua', 'cue': 'Đầu xe máy xuất hiện ở khúc cua khuất tầm nhìn', 'group': 'intersection'},
    35: {'ch': 2, 'title': 'Xe con phía trước phanh gấp vì gặp ổ gà lớn', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},
    36: {'ch': 2, 'title': 'Xe máy từ đường đất nông thôn lao thẳng ra đường nhựa', 'cue': 'Bánh trước xe máy vừa chạm vào mép đường nhựa', 'group': 'intersection'},
    37: {'ch': 2, 'title': 'Khúc cua nguy hiểm có đống gạch xây dựng lấn đường', 'cue': 'Đầu xe máy ngược chiều xuất hiện sau đống gạch', 'group': 'intersection'},
    38: {'ch': 2, 'title': 'Xe tải ngược chiều lấn làn ở khúc cua gấp', 'cue': 'Đầu xe tải ngược chiều vừa đè lên vạch tim đường', 'group': 'lane_cross'},
    39: {'ch': 2, 'title': 'Xe tải chở đất từ mỏ đất rẽ vào đường chính', 'cue': 'Bánh trước xe tải đất vừa chạm mặt đường chính', 'group': 'intersection'},
    40: {'ch': 2, 'title': 'Khúc cua khuất tầm nhìn gặp trâu bò chắn đường', 'cue': 'Thân con trâu xuất hiện trọn vẹn sau rặng cây', 'group': 'animal'},
    41: {'ch': 2, 'title': 'Xe con phía trước phanh gấp vì đường bị sạt lở', 'cue': 'Đèn phanh đỏ xe con phía trước vừa sáng', 'group': 'brake_light'},
    42: {'ch': 2, 'title': 'Đoạn đường hẹp gặp xe máy đi ngược chiều tốc độ cao', 'cue': 'Đầu xe máy vừa xuất hiện sau lùm tre', 'group': 'cut_in'},
    43: {'ch': 2, 'title': 'Xe tải chở mía quá tải nghiêng ngả ở khúc cua', 'cue': 'Thân xe tải mía bắt đầu nghiêng lấn sang làn bạn', 'group': 'lane_cross'},

    # ================= CHƯƠNG 3: ĐƯỜNG CAO TỐC (44 - 63) =================
    44: {'ch': 3, 'title': 'Xe con chuyển làn cắt mặt không xi-nhan trên cao tốc', 'cue': 'Bánh trước xe con vừa đè vạch đứt chuyển làn sang làn bạn', 'group': 'cut_in'},
    45: {'ch': 3, 'title': 'Xe tải phía trước phanh gấp tránh sự cố', 'cue': 'Đèn phanh đỏ xe tải vừa chớm sáng lên', 'group': 'brake_light'},
    46: {'ch': 3, 'title': 'Xe con vượt phải tạt đầu nguy hiểm trên cao tốc', 'cue': 'Đầu xe con bên phải vừa chớm vượt qua đầu xe bạn', 'group': 'cut_in'},
    47: {'ch': 3, 'title': 'Xe cứu thương xin vượt từ phía sau trên cao tốc', 'cue': 'Nhìn gương chiếu hậu thấy xe cứu thương bật đèn nháy', 'group': 'cut_in'},
    48: {'ch': 3, 'title': 'Xe con chuyển làn bất ngờ từ làn dừng khẩn cấp ra', 'cue': 'Bánh trước xe con vừa chạm vạch liền làn khẩn cấp', 'group': 'cut_in'},
    49: {'ch': 3, 'title': 'Xe tải phía trước phanh gấp rơi hàng hóa xuống đường', 'cue': 'Đèn phanh xe tải đỏ và thùng hàng bắt đầu rơi', 'group': 'brake_light'},
    50: {'ch': 3, 'title': 'Xe con phía trước phanh gấp vì gặp chướng ngại vật', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    51: {'ch': 3, 'title': 'Xe tải đi ngược chiều nguy hiểm trên cao tốc', 'cue': 'Đầu xe tải ngược chiều vừa xuất hiện từ xa ở làn bạn', 'group': 'lane_cross'},
    52: {'ch': 3, 'title': 'Xe con đi lùi ở nút giao ra khỏi cao tốc', 'cue': 'Đèn lùi trắng của xe con phía trước vừa bật sáng', 'group': 'cut_in'},
    53: {'ch': 3, 'title': 'Xe tải chuyển làn bất ngờ che khuất tầm nhìn', 'cue': 'Bánh xe tải vừa đè lên vạch phân làn cao tốc', 'group': 'cut_in'},
    54: {'ch': 3, 'title': 'Xe con từ đường nhánh nhập làn cao tốc với tốc độ chậm', 'cue': 'Đầu xe con vừa đè qua vạch phân làn nhập đường', 'group': 'intersection'},
    55: {'ch': 3, 'title': 'Xe con phía trước phanh gấp nhường xe nhập làn', 'cue': 'Đèn phanh đỏ xe con trước vừa sáng', 'group': 'brake_light'},
    56: {'ch': 3, 'title': 'Xe con gặp sự cố đỗ ở làn dừng khẩn cấp không đặt biển cảnh báo', 'cue': 'Đầu xe mình vừa ngang qua đuôi xe gặp sự cố', 'group': 'cut_in'},
    57: {'ch': 3, 'title': 'Xe tải phía trước phanh gấp do gặp công trường sửa đường', 'cue': 'Đèn phanh đỏ xe tải vừa bật sáng', 'group': 'brake_light'},
    58: {'ch': 3, 'title': 'Xe con chuyển làn liên tục vượt ẩu trên cao tốc', 'cue': 'Bánh xe con vừa chạm vạch đứt lách sang làn bạn', 'group': 'cut_in'},
    59: {'ch': 3, 'title': 'Xe con phía trước phanh gấp tránh mảnh lốp xe rơi trên đường', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},
    60: {'ch': 3, 'title': 'Xe tải từ làn khẩn cấp xi-nhan nhập làn cao tốc', 'cue': 'Bánh trước xe tải vừa chạm vạch phân cách làn', 'group': 'cut_in'},
    61: {'ch': 3, 'title': 'Xe con phía trước phanh gấp do xe khách dừng đón khách', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    62: {'ch': 3, 'title': 'Xe con đi ngược chiều ở làn ngoài cùng cao tốc', 'cue': 'Thấy rõ đầu xe con ngược chiều xuất hiện', 'group': 'lane_cross'},
    63: {'ch': 3, 'title': 'Gặp súc vật đi lạc trên đường cao tốc', 'cue': 'Con bò vừa bước chân qua dải phân cách vào làn xe', 'group': 'animal'},

    # ================= CHƯƠNG 4: ĐƯỜNG ĐÈO NÚI, SƯƠNG MÙ (64 - 73) =================
    64: {'ch': 4, 'title': 'Xe khách lấn làn ở khúc cua đường đèo hiểm trở', 'cue': 'Đầu xe khách vừa nhô ra khỏi khúc cua đè vạch vàng', 'group': 'lane_cross'},
    65: {'ch': 4, 'title': 'Khúc cua ban đêm gặp xe tải bật đèn pha chiếu xa lóa mắt', 'cue': 'Ánh đèn pha xe tải vừa lóe sáng ở mép cua', 'group': 'lane_cross'},
    66: {'ch': 4, 'title': 'Đoạn đường núi sạt lở đá rơi bất ngờ xuống đường', 'cue': 'Đá bắt đầu lăn từ sườn núi rơi xuống mặt đường', 'group': 'cut_in'},
    67: {'ch': 4, 'title': 'Xe con phía trước phanh gấp vì gặp đàn gia súc qua đèo', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},
    68: {'ch': 4, 'title': 'Đường đèo dốc sương mù dày đặc gặp xe tải đi chậm', 'cue': 'Bóng xe tải mờ ảo xuất hiện rõ dần trong sương mù', 'group': 'cut_in'},
    69: {'ch': 4, 'title': 'Xe tải mất phanh trôi dốc ở khúc đèo nguy hiểm', 'cue': 'Đầu xe tải trôi nhanh qua vạch tim đường', 'group': 'lane_cross'},
    70: {'ch': 4, 'title': 'Xe khách vượt xe tải ở khúc cua đè vạch liền', 'cue': 'Đầu xe khách vượt lên vừa lộ ra sau thân xe tải', 'group': 'lane_cross'},
    71: {'ch': 4, 'title': 'Xe con phía trước phanh gấp tránh tảng đá sạt lở', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    72: {'ch': 4, 'title': 'Đoạn đường đèo trơn trượt xe con đi trước bị mất lái quay ngang', 'cue': 'Đuôi xe con phía trước bắt đầu văng ngang sang làn bạn', 'group': 'cut_in'},
    73: {'ch': 4, 'title': 'Xe tải ngược chiều chở hàng quá khổ lấn hết mặt đường đèo', 'cue': 'Thùng xe tải ngược chiều vừa chạm vạch tim đường', 'group': 'lane_cross'},

    # ================= CHƯƠNG 5: ĐƯỜNG QUỐC LỘ, GIAO CẮT (74 - 90) =================
    74: {'ch': 5, 'title': 'Xe tải chở hàng từ cây xăng lao ra quốc lộ', 'cue': 'Đầu xe tải vừa chạm mép vỉa hè cây xăng', 'group': 'intersection'},
    75: {'ch': 5, 'title': 'Trẻ em đi xe đạp băng qua đường quốc lộ', 'cue': 'Bánh trước xe đạp vừa chạm dải vạch qua đường', 'group': 'pedestrian'},
    76: {'ch': 5, 'title': 'Xe máy từ ngõ phụ không giảm tốc lao thẳng ra', 'cue': 'Đầu xe máy vừa xuất hiện sau cổng làng', 'group': 'intersection'},
    77: {'ch': 5, 'title': 'Xe con phía trước phanh gấp nhường đường cho xe quay đầu', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},
    78: {'ch': 5, 'title': 'Xe máy lách qua dải phân cách sang đường ẩu', 'cue': 'Bánh xe máy vừa vượt qua khe hở dải phân cách', 'group': 'cut_in'},
    79: {'ch': 5, 'title': 'Xe tải phía trước phanh gấp gặp đoàn mô tô đi phượt', 'cue': 'Đèn phanh xe tải vừa sáng đỏ', 'group': 'brake_light'},
    80: {'ch': 5, 'title': 'Xe máy chở cồng kềnh rơi đồ xuống mặt đường quốc lộ', 'cue': 'Kiện hàng trên xe máy bắt đầu rơi chạm đất', 'group': 'cut_in'},
    81: {'ch': 5, 'title': 'Xe bán tải vượt xe tải ở đoạn đường cấm vượt', 'cue': 'Đầu xe bán tải vừa lách lên ngang thân xe tải', 'group': 'lane_cross'},
    82: {'ch': 5, 'title': 'Xe con phía trước phanh gấp do gặp chướng ngại vật', 'cue': 'Đèn phanh đỏ xe con trước vừa sáng', 'group': 'brake_light'},
    83: {'ch': 5, 'title': 'Gặp đàn cừu/dê băng qua đường quốc lộ', 'cue': 'Con cừu đầu tiên vừa đặt chân xuống mặt đường', 'group': 'animal'},
    84: {'ch': 5, 'title': 'Xe con phía trước phanh gấp tránh xe máy ngã', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    85: {'ch': 5, 'title': 'Xe tải chở gỗ rơi cây gỗ xuống mặt đường', 'cue': 'Khúc gỗ trên xe tải bắt đầu tuột dây rơi', 'group': 'cut_in'},
    86: {'ch': 5, 'title': 'Đoạn đường quốc lộ giao cắt đường sắt không có rào chắn', 'cue': 'Thấy đầu tàu hỏa vừa xuất hiện ở bên trái giao lộ', 'group': 'railway'},
    87: {'ch': 5, 'title': 'Đoàn xe máy chạy lấn làn dàn hàng ngang', 'cue': 'Nhóm xe máy vừa vượt qua dải phân cách tim đường', 'group': 'lane_cross'},
    88: {'ch': 5, 'title': 'Xe buýt dừng trả khách bất ngờ xi-nhan ra làn', 'cue': 'Đầu xe buýt vừa chớm đánh lái nhô ra khỏi điểm dừng', 'group': 'cut_in'},
    89: {'ch': 5, 'title': 'Xe đạp điện sang đường thiếu quan sát', 'cue': 'Bánh xe đạp điện vừa lăn xuống lòng đường quốc lộ', 'group': 'pedestrian'},
    90: {'ch': 5, 'title': 'Xe con phía trước phanh gấp vì gặp đèn đỏ ngã tư', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},

    # ================= CHƯƠNG 6: TAI NẠN GIAO THÔNG THỰC TẾ (91 - 120) =================
    91: {'ch': 6, 'title': 'Xe con lùi từ bãi đỗ xe ra đường chính che khuất tầm nhìn', 'cue': 'Đuôi xe con vừa nhô qua mép xe bên cạnh', 'group': 'intersection'},
    92: {'ch': 6, 'title': 'Xe khách lấn làn vượt xe tải ở đoạn dốc cua', 'cue': 'Đầu xe khách vừa lấn qua vạch tim đường', 'group': 'lane_cross'},
    93: {'ch': 6, 'title': 'Xe con phía trước phanh gấp trên cao tốc tránh xe chết máy', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    94: {'ch': 6, 'title': 'Xe tải chở hàng quá tải lật ở vòng xuyến ngã năm', 'cue': 'Thùng xe tải bắt đầu nghiêng chực lật', 'group': 'cut_in'},
    95: {'ch': 6, 'title': 'Người đi bộ bất ngờ trèo qua dải phân cách cao tốc', 'cue': 'Người đi bộ vừa chạm chân xuống làn đường cao tốc', 'group': 'pedestrian'},
    96: {'ch': 6, 'title': 'Xe con nổ lốp mất lái va vào dải phân cách giữa', 'cue': 'Xe con chao đảo bốc khói lốp', 'group': 'cut_in'},
    97: {'ch': 6, 'title': 'Xe khách vượt ẩu trong sương mù đối đầu xe bạn', 'cue': 'Bóng xe khách lấn làn hiện rõ trước mặt', 'group': 'lane_cross'},
    98: {'ch': 6, 'title': 'Xe con phía trước phanh gấp tránh người say rượu đi xe máy', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    99: {'ch': 6, 'title': 'Xe bồn xăng dầu va chạm bốc cháy ở ngã tư', 'cue': 'Đầu xe bồn vừa va chạm với chướng ngại vật', 'group': 'intersection'},
    100: {'ch': 6, 'title': 'Tàu hỏa chạy qua giao lộ có đèn đỏ nhấp nháy', 'cue': 'Đèn tín hiệu giao cắt đường sắt vừa bắt đầu chớp đỏ', 'group': 'railway'},
    101: {'ch': 6, 'title': 'Xe con vượt ẩu qua đường sắt suýt bị tàu đâm', 'cue': 'Xe con vừa cố vượt qua vạch dừng đường sắt', 'group': 'railway'},
    102: {'ch': 6, 'title': 'Xe máy đi ngược chiều trong hầm đường bộ', 'cue': 'Ánh đèn xe máy ngược chiều vừa xuất hiện trong hầm', 'group': 'lane_cross'},
    103: {'ch': 6, 'title': 'Xe con phía trước phanh gấp tránh xe chết máy trong hầm', 'cue': 'Đèn phanh đỏ xe con trước vừa bật sáng', 'group': 'brake_light'},
    104: {'ch': 6, 'title': 'Xe con chuyển làn bất ngờ trước lối vào trạm thu phí', 'cue': 'Bánh trước xe con vừa đè vạch đứt chuyển làn', 'group': 'cut_in'},
    105: {'ch': 6, 'title': 'Xe tải mất phanh đâm vào dải phân cách trạm thu phí', 'cue': 'Đầu xe tải vừa chồm lên dải phân cách bê tông', 'group': 'cut_in'},
    106: {'ch': 6, 'title': 'Xe khách chở công nhân lật ở khúc cua đường trơn', 'cue': 'Thân xe khách nghiêng hẳn sang làn đường', 'group': 'lane_cross'},
    107: {'ch': 6, 'title': 'Xe con phía trước phanh gấp tránh xe đi lùi', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    108: {'ch': 6, 'title': 'Xe máy chở bình gas rơi bình gas lăn ra đường', 'cue': 'Bình gas trên xe máy rơi xuống mặt đường', 'group': 'cut_in'},
    109: {'ch': 6, 'title': 'Xe trộn bê tông rẽ ẩu cuốn xe máy vào gầm', 'cue': 'Đầu xe trộn bê tông vừa đè vạch rẽ cắt mặt', 'group': 'intersection'},
    110: {'ch': 6, 'title': 'Xe container cán qua vạch dừng đèn đỏ ngã tư', 'cue': 'Bánh trước container vừa đè vạch dừng khi đèn vàng', 'group': 'intersection'},
    111: {'ch': 6, 'title': 'Xe khách lấn làn vượt xe tải đối đầu xe bạn', 'cue': 'Đầu xe khách vừa lộ diện hoàn toàn lấn sang làn bạn', 'group': 'lane_cross'},
    112: {'ch': 6, 'title': 'Xe con phía trước phanh gấp tránh chó chạy qua đường', 'cue': 'Đèn phanh đỏ xe con trước vừa chớm sáng', 'group': 'brake_light'},
    113: {'ch': 6, 'title': 'Xe buýt chở khách vượt ẩu chèn xe con vào rào chắn', 'cue': 'Thân xe buýt bắt đầu ép sát làn xe bạn', 'group': 'lane_cross'},
    114: {'ch': 6, 'title': 'Xe máy rẽ trái không quan sát trước đầu xe ben', 'cue': 'Bánh trước xe máy vừa rẽ cắt ngang đầu xe', 'group': 'cut_in'},
    115: {'ch': 6, 'title': 'Xe tải chở đất đứt phanh lao qua vòng xuyến', 'cue': 'Đầu xe tải vừa chồm vào khu vực đảo xuyến', 'group': 'intersection'},
    116: {'ch': 6, 'title': 'Xe con phía trước phanh gấp tránh đá rơi công trường', 'cue': 'Đèn phanh xe con trước vừa chớm đỏ', 'group': 'brake_light'},
    117: {'ch': 6, 'title': 'Xe container chuyển làn không nhường đường cho xe con', 'cue': 'Bánh trước container vừa đè lên vạch phân làn', 'group': 'cut_in'},
    118: {'ch': 6, 'title': 'Xe con đi lùi từ làn dừng khẩn cấp ra làn chạy', 'cue': 'Đèn lùi xe con sáng và đuôi xe chạm làn chính', 'group': 'cut_in'},
    119: {'ch': 6, 'title': 'Xe khách chạy quá tốc độ đâm vào rào chắn công trình', 'cue': 'Đầu xe khách chạm vào cọc tiêu công trình', 'group': 'cut_in'},
    120: {'ch': 6, 'title': 'Xe tải phía trước phanh gấp xe sau đâm dồn toa liên hoàn', 'cue': 'Đèn phanh đỏ xe tải trước vừa chớm sáng', 'group': 'brake_light'}
}

# 6 Nhóm điểm căn chuẩn lấy trọn 5 điểm
GOLDEN_CUE_GROUPS = {
    'brake_light': {
        'name': '🔴 ĐÈN PHANH ĐỎ XE TRƯỚC VỪA CHỚM SÁNG',
        'desc': 'Áp dụng cho mọi tình huống xe phía trước giảm tốc độ hoặc phanh gấp. Ngay khoảnh khắc đèn phanh sau xe chuyển sang màu đỏ là bấm phím SPACE lập tức.',
        'count': 32
    },
    'lane_cross': {
        'name': '🚗 XE NGƯỢC CHIỀU / VƯỢT XE ĐÈ VẠCH TIM ĐƯỜNG',
        'desc': 'Áp dụng khi gặp xe ngược chiều lấn làn hoặc xe khác vượt ẩu. Ngay khi bánh trước xe lấn đè lên vạch sơn tim đường là bấm SPACE ngay.',
        'count': 26
    },
    'pedestrian': {
        'name': '🚶 NGƯỜI ĐI BỘ / XE ĐẠP BƯỚC XUỐNG LÒNG ĐƯỜNG',
        'desc': 'Áp dụng khi người đi bộ qua đường hoặc khuất sau xe khác. Ngay khi người đi bộ vừa đặt 1 bước chân xuống mép đường nhựa là bấm SPACE ngay.',
        'count': 18
    },
    'intersection': {
        'name': '🛑 ĐẦU XE TỪ HẺM / ĐƯỜNG NHÁNH VỪA NHÔ RA',
        'desc': 'Áp dụng tại ngã ba, ngã tư hoặc xe từ gara lao ra. Bấm SPACE ngay khi đầu xe vừa chạm mép đường chính hoặc vừa ló ra sau góc tường / cột A.',
        'count': 22
    },
    'cut_in': {
        'name': '⚡ XE TẠT ĐẦU / CHUYỂN LÀN ĐÈ LÊN VẠCH PHÂN LÀN',
        'desc': 'Áp dụng cho xe chuyển làn ẩu hoặc xe máy tạt đầu. Bấm SPACE ngay khi bánh xe đầu tiên chớm đè lên vạch kẻ phân làn xe bạn.',
        'count': 14
    },
    'animal': {
        'name': '🐄 GIA SÚC (TRÂU, BÒ) VỪA BƯỚC LÊN MẶT ĐƯỜNG',
        'desc': 'Áp dụng cho đường nông thôn và đèo dốc. Bấm SPACE ngay khi con vật đầu tiên đặt chân lên mặt đường nhựa.',
        'count': 8
    }
}

CHAPTER_NAMES = {
    1: '🏙️ Chương 1: Đô thị & Khu đông dân cư (29 tình huống)',
    2: '🌾 Chương 2: Nông thôn & Đường gấp khúc (14 tình huống)',
    3: '🛣️ Chương 3: Cao tốc & Nhập làn (20 tình huống)',
    4: '⛰️ Chương 4: Đèo núi & Sương mù (10 tình huống)',
    5: '🚚 Chương 5: Quốc lộ & Giao cắt (17 tình huống)',
    6: '💥 Chương 6: Tai nạn giao thông thực tế (30 tình huống)'
}

def get_situation(sit_id):
    return SIMULATION_SITUATIONS.get(int(sit_id))

def get_situations_by_chapter(ch_num):
    return {k: v for k, v in SIMULATION_SITUATIONS.items() if v['ch'] == int(ch_num)}

def generate_mock_simulation_test():
    """Sinh đề thi thử 10 câu mô phỏng chuẩn ma trận Cục Đường Bộ (Đạt >= 35/50 điểm)"""
    # Ma trận: 2 câu Ch1, 1 câu Ch2, 2 câu Ch3, 1 câu Ch4, 2 câu Ch5, 2 câu Ch6
    ch_pools = {c: [k for k, v in SIMULATION_SITUATIONS.items() if v['ch'] == c] for c in range(1, 7)}
    selected = []
    selected.extend(random.sample(ch_pools[1], 2))
    selected.extend(random.sample(ch_pools[2], 1))
    selected.extend(random.sample(ch_pools[3], 2))
    selected.extend(random.sample(ch_pools[4], 1))
    selected.extend(random.sample(ch_pools[5], 2))
    selected.extend(random.sample(ch_pools[6], 2))
    random.shuffle(selected)
    return selected

def format_situation_detail(sit_id):
    s = get_situation(sit_id)
    if not s:
        return f"❌ Không tìm thấy tình huống mô phỏng #{sit_id}!"
    ch_name = CHAPTER_NAMES.get(s['ch'], f"Chương {s['ch']}")
    grp = GOLDEN_CUE_GROUPS.get(s['group'], {})
    grp_name = grp.get('name', 'Điểm căn an toàn')
    
    lines = [
        f"🎬 <b>TÌNH HUỐNG MÔ PHỎNG #{sit_id} / 120</b>",
        f"📂 <i>{ch_name}</i>",
        "━━━━━━━━━━━━━━━━━━━",
        f"📌 <b>Tình huống:</b> {s['title']}\n",
        "🎯 <b>ĐIỂM CĂN 5 ĐIỂM (BẤM PHÍM SPACE):</b>",
        f"👉 <b>{s['cue']}</b>\n",
        f"💡 <b>Quy tắc bắt điểm:</b> {grp_name}",
        "⚠️ <i>Mẹo: Bấm ngay khi thấy dấu hiệu trên để đạt trọn 5 điểm. Bấm quá sớm bị 0 điểm, bấm trễ bị 1-2 điểm!</i>"
    ]
    return "\n".join(lines)
