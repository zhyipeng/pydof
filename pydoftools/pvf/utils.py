def decrypt_bytes(data: bytes, crc: int) -> bytes:
    """对原始字节流进行初步解密"""
    key = 0x81A79011
    xor = crc ^ key
    int_num = len(data) // 4
    key_all = xor.to_bytes(4, 'little') * int_num
    value_xored_all = int.from_bytes(key_all, 'little') ^ int.from_bytes(data, 'little')
    mask1 = 0b00000000_00000000_00000000_00111111
    mask2 = 0b11111111_11111111_11111111_11000000
    mask1_all = int.from_bytes(mask1.to_bytes(4, 'little') * int_num, 'little')
    mask2_all = int.from_bytes(mask2.to_bytes(4, 'little') * int_num, 'little')
    value1 = value_xored_all & mask1_all
    value2 = value_xored_all & mask2_all
    value = value1 << 26 | value2 >> 6
    return value.to_bytes(4 * int_num, 'little')
