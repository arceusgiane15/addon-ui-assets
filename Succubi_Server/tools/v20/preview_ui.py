"""Render every Succubi form screen with sample data into one sheet: python3 preview_ui.py <out dir> <png>"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CORE_RP
from uirender import render, G

W = 'textures/ui/succubi_wallet/'
I = 'textures/ui/succubi_ui/icons/'
H = 'textures/ui/succubi_height/'
SCREENS = [
    ('server_form.long_form', {'title': '§lตั้งค่าของฉัน', 'body': '§7ตั้งค่าเฉพาะตัวคุณ ไม่มีผลกับคนอื่น', 'buttons': [
        ('§lแถบสถานะ (HUD): §aแสดง\n§7เลือด อาหาร น้ำ สติ เหนือช่องของ', I + 'hud'),
        ('§lปรับส่วนสูง · 180 ซม.\n§7ส่วนสูงมีผลกับเลือดสูงสุด', I + 'height'),
        ('§lวิธีใช้ปืน\n§7ยิง เล็ง รีโหลด', I + 'gun'),
        ('§lกลับไปกระเป๋าตังค์', I + 'back')]}),
    ('server_form.long_form', {'title': '§lตั้งค่าเซิร์ฟเวอร์§0§9§4§1', 'body': '§7สติของฉัน §d80§7/100   น้ำ §b18§7/20\n§7แพ็คปืน: §aเปิดอยู่§7 · สวิตช์มีผลกับทุกคนในโลก', 'buttons': [
        ('§lระบบค่าสติ: §aเปิด', ''), ('§lระบบหิวน้ำ: §aเปิด', ''), ('§lชื่อผู้เล่น: §aแสดงตลอด', ''),
        ('§lส่วนสูงอิสระ 1-500 ซม.: §cปิด\n§7ปิด = ผู้เล่นปรับได้ 140-220 ซม. ทุก 5 นาที', '')]}),
    ('server_form.long_form', {'title': '§lสร้างโซนกฎ§0§9§4§2', 'body': '§7แตะแต่ละแถวเพื่อเปลี่ยนค่า แล้วกด §aบันทึกโซน', 'buttons': [
        ('§lกฎของโซน\n§eห้ามวิ่ง', ''), ('§lรัศมี\n§e6 บล็อก', ''), ('§aบันทึกโซน', '')]}),
    ('server_form.long_form', {'title': '§lกระเป๋าตังค์§0§9§8§7', 'body': '§8ยอดในกระเป๋า\n§l§11,250 บาท§r\n\n§8เงินสดในตัว\n§l§4340 บาท', 'buttons': [
        ('ฝากเงิน', W + 'btn_deposit_s'), ('ถอนเงิน', W + 'btn_withdraw_s'), ('เครื่องราง', W + 'btn_amulet_s'), ('ตั้งค่า', W + 'btn_settings_s')]}),
    ('server_form.long_form', {'title': '§lปรับส่วนสูง§0§9§8§5h020rP', 'body': '§7ที่เลือก §d§l200 ซม.§r §7(ตอนนี้ 180)\n§7เลือดสูงสุด §c§l120 HP§r\n§7ปรับได้ 140-220 ซม. · 5 นาที/ครั้ง', 'buttons': [
        ('§l-10', H + 'btn_minus'), ('§l-1', H + 'btn_minus'), ('§l+1', H + 'btn_plus'), ('§l+10', H + 'btn_plus'),
        ('§lพิมพ์', H + 'btn_type'), ('§lรีเซ็ต', H + 'btn_reset'), ('§lยืนยัน', H + 'btn_confirm'), ('§lปิด', H + 'btn_close')]}),
    ('server_form.long_form', {'title': '§lถอนเงิน§0§9§8§6', 'body': '§8ยอดในกระเป๋า §l§11,250 บาท§r\n§8กดจำนวนที่จะถอน กดซ้ำได้เรื่อย ๆ', 'buttons': [
        (f'§l{a}', W + f'amt_{a}') for a in (1, 5, 10, 20, 50, 100, 500, 1000)] + [('§lกลับ', W + 'amt_back'), ('§lปิด', W + 'amt_close')]}),
]

if __name__ == '__main__':
    out, target = sys.argv[1], sys.argv[2]
    rp = os.path.join(out, CORE_RP)
    shots = []
    for ref, form in SCREENS:
        im, missing = render(rp, ref, form)
        if missing:
            print(form['title'][:20], 'missing:', missing[:8])
        shots.append(im)
    cols = 2
    w, h = shots[0].size
    sheet = Image.new('RGBA', (w * cols, h * ((len(shots) + cols - 1) // cols)), (40, 60, 50, 255))
    for i, s in enumerate(shots):
        sheet.alpha_composite(s, ((i % cols) * w, (i // cols) * h))
    sheet.save(target)
    print('saved', target, sheet.size)
