# 供 Breast_Care_Center 等 app 使用：為檔名附加 hash（用於衛教等 txt 檔）
import io
import os
import random
import zlib

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


def generate_captcha_image_bytes(code):
    """
    產生「第一種風格」驗證碼圖片：網格背景（淺紫/粉）、多色小點、多色波浪干擾線、五位數字。
    code: 驗證碼字串（如 "78855"）
    回傳: PNG 圖片 bytes，供 HttpResponse(content, content_type='image/png') 使用。
    """
    if Image is None:
        raise RuntimeError("PIL is required for captcha image generation")
    code = str(code)
    width, height = 160, 60
    # 淺紫/粉背景（第一種風格）
    bg = (random.randint(232, 242), random.randint(224, 236), random.randint(238, 248))
    image = Image.new('RGB', (width, height), color=bg)
    draw = ImageDraw.Draw(image)

    # 網格背景（方格紙感）
    grid_size = 6
    grid_color = (max(0, bg[0] - 18), max(0, bg[1] - 20), max(0, bg[2] - 15))
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    # 多色波浪/鋸齒干擾線（棕、深綠、紫、紅褐等）
    line_colors = [
        (101, 80, 60), (60, 90, 65), (120, 100, 145), (130, 75, 70),
        (85, 95, 75), (110, 85, 120), (90, 70, 65),
    ]
    for _ in range(7):
        points = []
        x, y = random.randint(0, width), random.randint(0, height)
        for _ in range(4 + random.randint(0, 2)):
            x = max(0, min(width, x + random.randint(-25, 25)))
            y = max(0, min(height, y + random.randint(-12, 12)))
            points.append((x, y))
        if len(points) >= 2:
            draw.line(points, fill=random.choice(line_colors), width=random.randint(1, 2))

    # 數字：每個字元不同深色、隨機歪斜（旋轉 -18～18 度）增加干擾
    char_width = width // len(code)
    digit_colors = [(50, 50, 55), (45, 75, 50), (75, 65, 45), (100, 55, 50), (60, 70, 90)]
    for i, char in enumerate(code):
        color = digit_colors[i % len(digit_colors)]
        # 在透明小圖上畫單一數字
        char_img = Image.new('RGBA', (40, 44), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((6, 2), char, font=font, fill=color)
        # 隨機旋轉造成歪斜
        angle = random.randint(-18, 18)
        char_img = char_img.rotate(angle, expand=False, resample=Image.BICUBIC, fillcolor=(255, 255, 255, 0))
        # 貼到主圖（旋轉後可能超出，取可貼範圍）
        px = char_width * i + random.randint(5, 10)
        py = random.randint(4, 12)
        image.paste(char_img, (px, py), char_img)

    # 多色小點雜訊（覆蓋在數字與背景上）
    speckle_colors = [
        (80, 60, 50), (70, 85, 60), (110, 95, 130), (120, 75, 70), (75, 75, 80),
        (95, 70, 100), (65, 80, 65), (90, 65, 70),
    ]
    for _ in range(600):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        image.putpixel((x, y), random.choice(speckle_colors))

    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)
    return buffer.getvalue()


def append_hash_to_filenames(directory, extension='.txt', separator='^'):
    """
    掃描 directory 下符合 extension 的檔案，若檔名中尚未包含 separator + hash，
    則根據檔案內容計算 CRC32 並重新命名為 原名 separator hash extension。
    若目錄不存在則略過。
    """
    if not directory or not os.path.isdir(directory):
        return
    for filename in os.listdir(directory):
        if not filename.endswith(extension):
            continue
        if separator in filename:
            continue
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            crc = zlib.crc32(content) & 0xFFFFFFFF
            hash_suffix = f"{crc:08x}"
            base = filename[: -len(extension)]
            new_name = f"{base}{separator}{hash_suffix}{extension}"
            new_path = os.path.join(directory, new_name)
            if new_path != filepath and not os.path.exists(new_path):
                os.rename(filepath, new_path)
        except Exception:
            pass
