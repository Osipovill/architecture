import struct

def create_bmp(filename, target_size):
    # BITMAPFILEHEADER (14 bytes)
    bf_type = b'BM'
    bf_size = target_size  # Общий размер файла
    bf_reserved1 = 0
    bf_reserved2 = 0
    bf_off_bits = 54  # Смещение до данных (14 + 40)

    # BITMAPINFOHEADER (40 bytes)
    bi_size = 40
    bi_width = 1
    bi_height = 1
    bi_planes = 1
    bi_bit_count = 24  # 24 бита на пиксель
    bi_compression = 0
    bi_size_image = 0  # Размер данных (0 для BI_RGB)
    bi_x_pels_per_meter = 0
    bi_y_pels_per_meter = 0
    bi_clr_used = 0
    bi_clr_important = 0

    # Упаковка заголовков
    file_header = struct.pack(
        '<2sIIII', bf_type, bf_size, bf_reserved1, bf_reserved2, bf_off_bits
    )
    info_header = struct.pack(
        '<IIIHHIIIIII',
        bi_size,
        bi_width,
        bi_height,
        bi_planes,
        bi_bit_count,
        bi_compression,
        bi_size_image,
        bi_x_pels_per_meter,
        bi_y_pels_per_meter,
        bi_clr_used,
        bi_clr_important,
    )

    # Данные: нули до достижения целевого размера
    data_size = target_size - len(file_header) - len(info_header)
    data = b'\x00' * data_size

    # Запись в файл
    with open(filename, 'wb') as f:
        f.write(file_header)
        f.write(info_header)
        f.write(data)

# Создание файлов
create_bmp('476.bmp', 90)
create_bmp('477.bmp', 477)
create_bmp('478.bmp', 478)