"""Generate a sample insurance claim form image for OCR testing."""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "sample_docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_claim_form_image():
    """Create an image of a filled insurance claim form (Vietnamese)."""
    # A4-ish dimensions at 150 DPI
    width, height = 1240, 1754
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Try to load a font that supports Vietnamese
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    font = None
    font_bold = None
    for fp in font_paths:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 22)
            break
    for fp in bold_font_paths:
        if os.path.exists(fp):
            font_bold = ImageFont.truetype(fp, 26)
            break

    if font is None:
        font = ImageFont.load_default()
    if font_bold is None:
        font_bold = font

    font_title = ImageFont.truetype(font_bold.path, 30) if hasattr(font_bold, 'path') else font_bold
    font_section = ImageFont.truetype(font_bold.path, 24) if hasattr(font_bold, 'path') else font_bold
    font_small = ImageFont.truetype(font.path, 18) if hasattr(font, 'path') else font

    y = 40
    margin = 60

    # Border
    draw.rectangle([30, 30, width - 30, height - 30], outline="black", width=2)

    # Header
    draw.text((width // 2 - 250, y), "TỔNG CÔNG TY BẢO HIỂM TOÀN CẦU", font=font_bold, fill="black", anchor=None)
    y += 40
    draw.text((width // 2 - 120, y), "GlobalCare Insurance", font=font_small, fill="gray")
    y += 50

    # Title
    draw.text((width // 2 - 220, y), "ĐƠN YÊU CẦU BỒI THƯỜNG", font=font_title, fill="black")
    y += 40
    draw.text((width // 2 - 180, y), "BẢO HIỂM XE Ô TÔ", font=font_title, fill="black")
    y += 50

    # Form number
    draw.text((margin, y), "Số đơn: CLM-2024-00891", font=font, fill="black")
    draw.text((width - 350, y), "Ngày lập: 20/08/2024", font=font, fill="black")
    y += 50

    # Divider
    draw.line([(margin, y), (width - margin, y)], fill="black", width=2)
    y += 20

    # Section 1
    draw.text((margin, y), "I. THÔNG TIN NGƯỜI YÊU CẦU BỒI THƯỜNG", font=font_section, fill="black")
    y += 40

    fields_1 = [
        ("Họ và tên:", "Trần Minh Đức"),
        ("Số hợp đồng:", "AUTO-2024-005678"),
        ("Số CCCD:", "079090123456"),
        ("Số điện thoại:", "0908-123-456"),
        ("Địa chỉ:", "123 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh"),
    ]

    for label, value in fields_1:
        draw.text((margin + 20, y), label, font=font, fill="black")
        draw.text((margin + 250, y), value, font=font, fill="navy")
        y += 35

    y += 20

    # Section 2
    draw.text((margin, y), "II. THÔNG TIN XE", font=font_section, fill="black")
    y += 40

    fields_2 = [
        ("Biển số xe:", "51A-123.45"),
        ("Nhãn hiệu:", "Toyota Camry 2.5Q - 2023"),
        ("Màu xe:", "Đen"),
        ("Số km hiện tại:", "15.230 km"),
    ]

    for label, value in fields_2:
        draw.text((margin + 20, y), label, font=font, fill="black")
        draw.text((margin + 250, y), value, font=font, fill="navy")
        y += 35

    y += 20

    # Section 3
    draw.text((margin, y), "III. THÔNG TIN TAI NẠN / TỔN THẤT", font=font_section, fill="black")
    y += 40

    fields_3 = [
        ("Ngày xảy ra:", "18/08/2024"),
        ("Giờ xảy ra:", "14:30"),
        ("Địa điểm:", "Ngã tư Điện Biên Phủ - Hai Bà Trưng, Q.3, TP.HCM"),
    ]

    for label, value in fields_3:
        draw.text((margin + 20, y), label, font=font, fill="black")
        draw.text((margin + 250, y), value, font=font, fill="navy")
        y += 35

    y += 10
    draw.text((margin + 20, y), "Mô tả sự việc:", font=font, fill="black")
    y += 35

    description_lines = [
        "Xe đang lưu thông trên đường Điện Biên Phủ hướng từ Q.1 đi Q.Bình Thạnh,",
        "tốc độ khoảng 40km/h. Tại ngã tư Hai Bà Trưng, một xe máy từ đường",
        "Hai Bà Trưng vượt đèn đỏ và va chạm vào hông bên phải xe. Lái xe đã",
        "phanh gấp nhưng không tránh kịp. Xe máy ngã, người điều khiển bị xây",
        "xát nhẹ. Xe ô tô bị móp cửa sau bên phải và trầy xước hông phải.",
    ]

    for line in description_lines:
        draw.text((margin + 40, y), line, font=font_small, fill="black")
        y += 28

    y += 20

    # Section 4
    draw.text((margin, y), "IV. THIỆT HẠI ƯỚC TÍNH", font=font_section, fill="black")
    y += 40

    damages = [
        ("1. Móp cửa sau bên phải:", "8.500.000 VNĐ"),
        ("2. Trầy xước hông phải (cần sơn lại):", "4.200.000 VNĐ"),
        ("3. Gương chiếu hậu phải bị vỡ:", "2.800.000 VNĐ"),
        ("Tổng thiệt hại ước tính:", "15.500.000 VNĐ"),
    ]

    for label, value in damages:
        if "Tổng" in label:
            draw.text((margin + 20, y), label, font=font_bold, fill="black")
            draw.text((margin + 500, y), value, font=font_bold, fill="red")
        else:
            draw.text((margin + 20, y), label, font=font, fill="black")
            draw.text((margin + 500, y), value, font=font, fill="navy")
        y += 35

    y += 20

    # Section 5
    draw.text((margin, y), "V. HỒ SƠ ĐÍNH KÈM", font=font_section, fill="black")
    y += 40

    attachments = [
        "[✓] Bản sao Giấy phép lái xe",
        "[✓] Bản sao Đăng ký xe",
        "[✓] Biên bản tai nạn giao thông (Công an Q.3 lập)",
        "[✓] Hình ảnh thiệt hại (8 ảnh)",
        "[✓] Báo giá sửa chữa từ garage Toyota Đông Sài Gòn",
        "[ ] Hóa đơn sửa chữa (sẽ bổ sung sau khi sửa)",
    ]

    for item in attachments:
        draw.text((margin + 20, y), item, font=font, fill="black")
        y += 32

    y += 30

    # Signature area
    draw.line([(margin, y), (width - margin, y)], fill="black", width=1)
    y += 20

    draw.text((margin + 20, y), "Người yêu cầu bồi thường", font=font, fill="black")
    draw.text((width - 350, y), "Xác nhận của công ty BH", font=font, fill="black")
    y += 80

    draw.text((margin + 50, y), "Trần Minh Đức", font=font_bold, fill="navy")
    draw.text((width - 320, y), "(Đang xử lý)", font=font_small, fill="gray")
    y += 30
    draw.text((margin + 20, y), "Ngày: 20/08/2024", font=font_small, fill="black")

    # Save
    filepath = os.path.join(OUTPUT_DIR, "Don_Yeu_Cau_Boi_Thuong_CLM2024_00891.png")
    img.save(filepath, "PNG", quality=95)
    print(f"✓ Created: {filepath}")


if __name__ == "__main__":
    print("Generating sample claim form image...\n")
    create_claim_form_image()
    print(f"\n✅ Done! Image saved in '{OUTPUT_DIR}/' folder.")
