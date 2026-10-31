import struct
p = r'C:/Users/Christian/.gemini/antigravity/brain/f16d854a-fa94-47aa-87d4-a1955f81bb35/.user_uploaded/media_1793423350824_4dc8bc3f.jpg'
with open(p, 'rb') as f:
    data = f.read()
i = 0
while i < len(data) - 9:
    if data[i] == 0xff and data[i+1] in (0xc0, 0xc1, 0xc2):
        h, w = struct.unpack('>HH', data[i+5:i+9])
        print(f"Image Resolution: {w} x {h}")
        break
    i += 1

