"""v1.0.16 content: book stall + books, amulet stall + amulets, horror-kit props.
Importing this module registers the new goods / stands / shops in data_extra + stands (before the build runs)."""
import math
from PIL import Image, ImageDraw
from boxkit import solid, vgrad, label, cross, stripes, per_face, grid_goods, shade, dots, _font
import data_extra
from data_extra import WHITE, BLACK, GREEN, DGREEN, RED, BLUE, ORANGE, YELLOW, box, centred
import stands

GOLD, DGOLD, CREAM, WOOD, DWOOD = (232, 186, 60), (150, 110, 30), (246, 236, 210), (150, 104, 60), (96, 62, 34)


# ------------------------------------------------------------------ books
def book_model(cover, title, fg=WHITE, thick=1.4, w=4.6, h=6.2):
    front = label(cover, [(title, fg, 1.0)], bands=[(0.0, 0.08, shade(cover, 0.7)), (0.92, 1, shade(cover, 0.7))], size=0.17, top=0.45)
    pages = solid((244, 240, 228))
    return [centred(w, h, thick, paint=per_face(pages, north=front, south=solid(cover), east=solid(shade(cover, 0.8)),
                                                 west=pages, up=pages, down=pages))]


def newspaper_model():
    front = label((238, 236, 228), [("ข่าวสด", BLACK, 1.1), ("SUCCUBI", RED, 0.7)], bands=[(0.0, 0.2, (40, 40, 40))],
                  icon=lambda d, w, h: [d.line([(w * 0.1, h * y), (w * 0.9, h * y)], fill=(120, 120, 120, 255), width=max(1, h // 60))
                                        for y in (0.6, 0.68, 0.76, 0.84)], size=0.15, top=0.36)
    return [centred(5.2, 6.8, 0.4, paint=per_face(solid((230, 228, 220)), north=front))]


def coloring_model():
    cover = label((250, 250, 250), [("ระบายสี", (230, 80, 120), 1.0)], icon=dots([(240, 80, 80), (80, 160, 240), (250, 200, 40), (80, 190, 90)], n=4, cy=0.78, r=0.08), size=0.16, top=0.4)
    P = [centred(5.0, 6.0, 0.6, paint=per_face(solid((250, 250, 250)), north=cover))]
    for i, c in enumerate([(230, 60, 60), (60, 140, 230), (250, 200, 40)]):
        P.append(centred(0.6, 3.2, 0.6, y=0.2, x=2.9 + i * 0.7, z=-0.2, paint=solid(c)))
    return P


BOOKS = [
    dict(key="book_newspaper", name="หนังสือพิมพ์รายวัน", short="หนังสือพิมพ์", en="Daily Newspaper", price=20, sanity=3, cooldown=0, consumed=True,
         model=newspaper_model, special="news", desc="ข่าวรอบเซิร์ฟ อ่านจบแล้วทิ้ง"),
    dict(key="book_comic", name="การ์ตูนแก๊กขำกลิ้ง", short="การ์ตูนแก๊ก", en="Gag Comic", price=65, sanity=10, cooldown=10, consumed=False,
         model=lambda: book_model((250, 200, 40), "ขำกลิ้ง!", fg=RED), desc="หัวเราะจนลืมกลัว"),
    dict(key="book_travel", name="นิตยสารเที่ยวทั่วไทย", short="นิตยสารเที่ยว", en="Travel Magazine", price=89, sanity=8, cooldown=10, consumed=False,
         model=lambda: book_model((40, 150, 200), "เที่ยวไทย", thick=0.8), desc="ภาพทะเล ภูเขา อ่านแล้วใจฟู"),
    dict(key="book_romance", name="นิยายรัก 'ใต้แสงจันทร์'", short="นิยายรัก", en="Romance Novel", price=259, sanity=15, cooldown=20, consumed=False,
         model=lambda: book_model((230, 120, 160), "ใต้แสงจันทร์", thick=2.0), desc="หวานจนลืมความมืด"),
    dict(key="book_mystery", name="นิยายสืบสวน 'คดีบ้านร้าง'", short="นิยายสืบสวน", en="Mystery Novel", price=289, sanity=15, cooldown=20, consumed=False,
         model=lambda: book_model((50, 50, 70), "คดีบ้านร้าง", fg=(240, 200, 80), thick=2.0), desc="ลุ้นจนวางไม่ลง"),
    dict(key="book_dharma", name="หนังสือธรรมะ 'ใจสงบ'", short="หนังสือธรรมะ", en="Dharma Book", price=99, sanity=20, cooldown=30, consumed=False,
         model=lambda: book_model((240, 150, 40), "ใจสงบ", thick=1.2), special="calm",
         desc="อ่านจบแล้วไม่หวั่นคำสาปตุ๊กตา 30 นาที"),
    dict(key="book_prayer", name="หนังสือสวดมนต์", short="สวดมนต์", en="Prayer Book", price=35, sanity=6, cooldown=10, consumed=False,
         model=lambda: book_model((200, 40, 40), "บทสวดมนต์", fg=(250, 220, 120), w=3.8, h=5.4), special="ward",
         desc="อ่านจบแล้วกันเหตุการณ์ผิดปกติครั้งถัดไป"),
    dict(key="book_coloring", name="สมุดระบายสี + สีเทียน", short="สมุดระบายสี", en="Coloring Book", price=45, sanity=8, cooldown=10, consumed=False,
         model=coloring_model, desc="ระบายสีเพลินๆ คลายเครียด"),
    dict(key="book_survival", name="คู่มือเอาชีวิตรอดฉบับพกพา", short="คู่มือรอด", en="Pocket Survival Guide", price=199, sanity=5, cooldown=5, consumed=False,
         model=lambda: book_model((60, 110, 60), "คู่มือรอด", w=4.0, h=5.6), special="guide", desc="สรุประบบของเซิร์ฟ อ่านแล้วอุ่นใจ"),
    dict(key="book_ghost", name="หนังสือเล่มดำ 'เรื่องเล่าต้องห้าม'", short="เล่มดำ", en="The Black Book", price=159, sanity=-10, cooldown=15, consumed=False,
         model=lambda: book_model((20, 16, 20), "ต้องห้าม", fg=(200, 30, 30), thick=1.8), special="cursed",
         desc="§cอย่าอ่านคนเดียว... สติลด และเจอเรื่องแปลก"),
]

# pages shown when reading (newspaper pages are made up at read time)
PAGES = {
    "book_comic": ["ลุงแดงซื้อตู้เย็นใหม่ แต่ลืมว่าบ้านไม่มีไฟฟ้า... ตอนนี้ใช้เป็นตู้เก็บรองเท้าแทน",
                   "นักรบเอาเข็มฉีดยาไปแทงกล้วย แล้วบอกว่า 'ช่วยชีวิตมันไว้แล้ว!' ... กล้วยไม่ได้ป่วยครับ",
                   "ผีบ้านร้างออกมาหลอก แต่เจอหนี้บัตรเครดิตของเจ้าของบ้าน ผีเลยร้องไห้กลับเข้าไปเอง"],
    "book_travel": ["ทะเลอันดามันเช้านี้ใสจนเห็นปลาว่ายรอบเท้า เสียงคลื่นทำให้ลืมทุกเรื่อง",
                    "ดอยอินทนนท์ ทะเลหมอกลอยต่ำ กาแฟร้อนหนึ่งแก้วกับลมหนาว",
                    "ตลาดน้ำยามเย็น ก๋วยเตี๋ยวเรือชามเล็ก กับแสงไฟตะเกียงริมคลอง"],
    "book_romance": ["คืนนั้นดวงจันทร์เต็มดวง เธอยื่นร่มให้เขาทั้งที่ฝนไม่ได้ตก...",
                     "'ถ้าวันหนึ่งฉันหลงทาง เธอจะตามหาไหม' — 'ฉันจะเป็นแสงไฟให้เธอเดินกลับมา'",
                     "ตอนจบ ทั้งคู่นั่งดูพระจันทร์ด้วยกัน และไม่มีใครกลัวความมืดอีกเลย"],
    "book_mystery": ["บ้านร้างหลังนั้นมีรอยเท้าเปียกทั้งที่ฝนไม่ตกมาสามวัน นักสืบก้มลงดู...",
                     "เบาะแสชิ้นสุดท้ายคือกุญแจที่ไขได้ทุกประตู ยกเว้นประตูห้องใต้ดิน",
                     "คนร้ายคือ... ภารโรง! คดีปิด นักสืบกลับบ้านไปกินข้าวไข่เจียวสูตรผู้บัญชาการ"],
    "book_dharma": ["ความกลัวเกิดจากใจ เมื่อรู้ทันใจ ความกลัวก็เบาบางลง",
                    "หายใจเข้า รู้ว่าหายใจเข้า หายใจออก รู้ว่าหายใจออก",
                    "สิ่งที่มองไม่เห็นไม่อาจทำร้ายใจที่สงบได้ — ขออนุโมทนา"],
    "book_prayer": ["อิติปิ โส ภะคะวา อะระหัง สัมมาสัมพุทโธ...",
                    "สวากขาโต ภะคะวะตา ธัมโม สันทิฏฐิโก อะกาลิโก...",
                    "ขอคุณพระคุ้มครอง ให้แคล้วคลาดจากสิ่งไม่ดีทั้งปวง สาธุ"],
    "book_coloring": ["หน้า 1: รูปแมวนอนบนหมอน — คุณระบายสีส้มลงไปช้าๆ",
                      "หน้า 2: รูปดอกบัวในบึง — สีชมพูอ่อนกับเขียวใบบัว",
                      "หน้า 3: รูปบ้านหลังเล็กมีไฟเปิดอยู่ — อบอุ่นดีจัง"],
    "book_survival": ["สติ (วงสมอง): กินของอร่อย นอนหลับ อ่านหนังสือ กอดตุ๊กตา = สติเพิ่ม | โดนตี อยู่ใกล้มอนสเตอร์ เจอเรื่องแปลก = สติลด",
                      "น้ำ (วงหยดน้ำ): ของเผ็ด/เค็มทำให้คอแห้ง ซุปกับเครื่องดื่มช่วยได้ | ร้านยามี ORS กับยาแก้ไอ",
                      "เครื่องราง: เปิดกระเป๋าตังค์ > เครื่องราง ใส่ได้ 4 ชิ้น | ถ้าเห็นป้ายกฎ... ทำตามกฎเสมอ"],
    "book_ghost": ["มีคนเขียนไว้ด้วยลายมือสั่นเทา: 'ถ้าได้ยินเสียงเคาะสามครั้ง อย่าเปิดประตู'",
                   "'ถ้าเห็นรูปปั้นขยับ อย่ากะพริบตา อย่าหันหลัง'",
                   "หน้าสุดท้ายว่างเปล่า... แต่กระดาษชื้นเหมือนเพิ่งมีคนแตะ"],
}


# ------------------------------------------------------------------ amulets (2D icons)
def _icon(draw_fn):
    def make():
        S = 256
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        draw_fn(d, S)
        return im.resize((64, 64), Image.LANCZOS)
    return make


def _medal(d, S, rim, inner):
    d.rounded_rectangle([56, 30, 200, 226], radius=40, fill=rim + (255,))
    d.rounded_rectangle([72, 46, 184, 210], radius=30, fill=inner + (255,))
    d.ellipse([112, 6, 144, 38], outline=rim + (255,), width=8)


def _figure(d, col, cx=128, cy=128, s=1.0, hand=False):
    d.ellipse([cx - 16 * s, cy - 58 * s, cx + 16 * s, cy - 26 * s], fill=col + (255,))
    d.polygon([(cx, cy - 30 * s), (cx - 42 * s, cy + 56 * s), (cx + 42 * s, cy + 56 * s)], fill=col + (255,))
    if hand:
        d.rectangle([cx + 20 * s, cy - 40 * s, cx + 30 * s, cy + 4 * s], fill=col + (255,))


def _takrut(d, S):
    d.rounded_rectangle([40, 104, 216, 152], radius=24, fill=(196, 150, 70, 255))
    for x in range(70, 200, 22):
        d.line([(x, 108), (x, 148)], fill=(140, 100, 40, 255), width=4)
    d.line([(20, 128), (236, 128)], fill=(200, 30, 40, 255), width=8)


def _bia(d, S):
    d.ellipse([70, 60, 186, 200], fill=(250, 246, 232, 255), outline=(200, 190, 160, 255), width=6)
    d.line([(128, 76), (128, 184)], fill=(150, 130, 100, 255), width=8)
    d.arc([40, 30, 216, 226], 200, 340, fill=(200, 30, 40, 255), width=8)


def _pha_yant(d, S):
    d.rectangle([48, 48, 208, 208], fill=(246, 240, 226, 255), outline=(200, 30, 40, 255), width=8)
    for i in range(5):
        y = 70 + i * 28
        d.line([(66, y), (190, y)], fill=(200, 30, 40, 255), width=5)
    d.ellipse([108, 108, 148, 148], outline=(200, 30, 40, 255), width=6)


def _fang(d, S):
    d.polygon([(96, 50), (160, 50), (140, 210), (122, 226)], fill=(250, 248, 236, 255))
    d.rectangle([90, 36, 166, 64], fill=GOLD + (255,))


def _eye(d, S):
    d.ellipse([30, 30, 226, 226], fill=GOLD + (255,))
    d.ellipse([54, 90, 202, 166], fill=(255, 255, 255, 255))
    d.ellipse([104, 98, 152, 158], fill=(40, 150, 90, 255)); d.ellipse([120, 114, 136, 142], fill=(10, 10, 10, 255))


def _doll(d, S):
    br = (140, 100, 60, 255)
    d.ellipse([88, 30, 168, 110], fill=br)
    d.rectangle([98, 100, 158, 190], fill=br)
    d.rectangle([56, 112, 200, 136], fill=br)
    d.rectangle([98, 186, 118, 230], fill=br); d.rectangle([138, 186, 158, 230], fill=br)
    for (x, y) in ((110, 60), (142, 60)):
        d.line([(x - 8, y - 8), (x + 8, y + 8)], fill=(20, 20, 20, 255), width=5); d.line([(x - 8, y + 8), (x + 8, y - 8)], fill=(20, 20, 20, 255), width=5)
    for (x0, y0, x1, y1) in ((150, 120, 190, 90), (100, 150, 70, 130), (140, 170, 180, 190)):
        d.line([(x0, y0), (x1, y1)], fill=(200, 200, 210, 255), width=5); d.ellipse([x1 - 7, y1 - 7, x1 + 7, y1 + 7], fill=(220, 30, 40, 255))


def _talisman(d, S):
    d.rectangle([84, 20, 172, 236], fill=(250, 214, 60, 255))
    d.line([(128, 40), (128, 216)], fill=(200, 30, 30, 255), width=6)
    for y in (60, 100, 140, 180):
        d.line([(100, y), (156, y + 10)], fill=(200, 30, 30, 255), width=6)
    d.ellipse([108, 188, 148, 228], outline=(200, 30, 30, 255), width=5)


def _leklai(d, S):
    d.ellipse([34, 34, 222, 222], fill=(40, 30, 30, 255), outline=GOLD + (255,), width=10)
    d.rounded_rectangle([96, 50, 160, 206], radius=30, fill=(96, 100, 116, 255))
    d.rounded_rectangle([108, 64, 128, 190], radius=10, fill=(200, 206, 226, 255))


def _moon(d, S):
    d.ellipse([40, 40, 216, 216], fill=(90, 130, 220, 255))
    d.ellipse([60, 60, 196, 196], fill=(150, 190, 250, 255))
    d.ellipse([96, 70, 180, 170], fill=(250, 246, 210, 255)); d.ellipse([118, 62, 196, 160], fill=(150, 190, 250, 255))


def _hanuman(d, S):
    d.ellipse([40, 40, 216, 216], fill=(200, 40, 40, 255))
    d.ellipse([78, 70, 178, 186], fill=(250, 250, 250, 255))
    d.ellipse([100, 104, 120, 124], fill=(20, 20, 20, 255)); d.ellipse([136, 104, 156, 124], fill=(20, 20, 20, 255))
    d.rectangle([112, 150, 144, 160], fill=(200, 40, 40, 255))


def _rice(d, S):
    d.rounded_rectangle([50, 30, 206, 226], radius=36, fill=(60, 150, 70, 255))
    for i in range(7):
        a = -0.5 + i * 0.17
        d.line([(128, 200), (128 + math.sin(a) * 70, 80 - math.cos(a) * 30)], fill=(250, 214, 80, 255), width=8)


AMULETS = [
    dict(key="amulet_luang_por", name="พระเครื่องหลวงพ่อ", short="พระหลวงพ่อ", en="Luang Por Amulet", price=1299,
         icon=_icon(lambda d, S: (_medal(d, S, GOLD, (120, 80, 40)), _figure(d, GOLD))), effect="ฟื้นเลือด +1 ทุก 4 วินาที"),
    dict(key="amulet_takrut", name="ตะกรุดโทน", short="ตะกรุดโทน", en="Takrut", price=899, icon=_icon(_takrut),
         effect="สติฟื้นเอง +3/นาที, เรื่องแปลกเสียสติน้อยลง 30%"),
    dict(key="amulet_bia_kae", name="เบี้ยแก้", short="เบี้ยแก้", en="Bia Kae Cowrie", price=699, icon=_icon(_bia),
         effect="ล้างพิษ คลื่นไส้ และอาการเหี่ยวเฉาเองอัตโนมัติ"),
    dict(key="amulet_pha_yant", name="ผ้ายันต์ห้าแถว", short="ผ้ายันต์", en="Five-Row Yantra Cloth", price=1599, icon=_icon(_pha_yant),
         effect="ทนทาน (Resistance I) ตลอดเวลา"),
    dict(key="amulet_khiao_suea", name="เขี้ยวเสือ", short="เขี้ยวเสือ", en="Tiger Fang", price=1199, icon=_icon(_fang),
         effect="วิ่งเร็ว (Speed I) ตลอดเวลา"),
    dict(key="amulet_nang_kwak", name="นางกวัก", short="นางกวัก", en="Nang Kwak", price=999,
         icon=_icon(lambda d, S: (_medal(d, S, GOLD, (180, 40, 60)), _figure(d, GOLD, hand=True))), effect="ลดราคาทุกร้าน 10%"),
    dict(key="amulet_kuman_thong", name="กุมารทอง", short="กุมารทอง", en="Kuman Thong", price=2499,
         icon=_icon(lambda d, S: (_medal(d, S, (40, 40, 40), (70, 60, 50)), _figure(d, GOLD, s=0.9))), effect="ทุก 15 นาทีได้เงินสด 10-60 บาท"),
    dict(key="amulet_ta_thip", name="ตาทิพย์", short="ตาทิพย์", en="Divine Eye", price=799, icon=_icon(_eye),
         effect="มองในที่มืด (Night Vision) ตลอดเวลา"),
    dict(key="amulet_cursed_doll", name="ตุ๊กตาสาปแช่ง", short="ตุ๊กตาสาป", en="Cursed Doll", price=666, icon=_icon(_doll),
         effect="คนรอบตัว 20 บล็อกเจอเรื่องแปลกเร็วขึ้น 2 เท่า (ผู้ใส่เสียสติช้าๆ)"),
    dict(key="amulet_yant_kan_phi", name="ยันต์กันผี", short="ยันต์กันผี", en="Ghost Ward Talisman", price=1499, icon=_icon(_talisman),
         effect="เรื่องแปลกช้าลงครึ่งหนึ่ง เสียสติน้อยลงครึ่ง กันคำสาปตุ๊กตา"),
    dict(key="amulet_lek_lai", name="เหล็กไหล", short="เหล็กไหล", en="Lek Lai", price=1799, icon=_icon(_leklai),
         effect="ทนไฟ (Fire Resistance) ตลอดเวลา"),
    dict(key="amulet_moon", name="ลูกแก้วจันทรา", short="แก้วจันทรา", en="Moon Crystal", price=1099, icon=_icon(_moon),
         effect="กลางคืนสติฟื้นเอง +6/นาที"),
    dict(key="amulet_hanuman", name="หนุมานเชิญธง", short="หนุมาน", en="Hanuman", price=1999, icon=_icon(_hanuman),
         effect="แรงขึ้น (Strength I) ตลอดเวลา"),
    dict(key="amulet_mae_pho", name="แม่โพสพ", short="แม่โพสพ", en="Mae Phosop", price=599, icon=_icon(_rice),
         effect="อิ่มนาน: เติมความอิ่มนิดหน่อยทุกนาที"),
]


# ------------------------------------------------------------------ stands
def book_stall():
    table, cloth = WOOD, (170, 40, 40)
    colors = [(230, 80, 80), (60, 140, 230), (250, 200, 40), (80, 190, 90), (240, 150, 40), (150, 80, 180), (40, 40, 60), (230, 120, 160)]
    P = [centred(30, 12, 12, z=-2, paint=per_face(solid(table), north=label(cloth, [("แผงหนังสือ", CREAM, 1.0)], bands=[(0.0, 0.12, GOLD), (0.88, 1, GOLD)], size=0.34), up=solid(shade(table, 1.1))))]
    for i in range(7):  # book piles on the table
        c = colors[i % len(colors)]
        P.append(centred(3.2, 1.0 + (i % 3) * 0.8, 4.2, y=12, x=-12 + i * 4, z=-4, paint=per_face(solid(c), up=solid(CREAM))))
    # slanted magazine rack behind
    P.append(centred(30, 24, 2, y=0, z=5, paint=per_face(solid(DWOOD), north=grid_goods(colors, rows=4, cols=8, bg=(80, 52, 30), gap=0.18))))
    P.append(centred(30, 5, 1.5, y=26, z=5, paint=per_face(solid(DWOOD), north=label((80, 52, 30), [("หนังสือ · นิตยสาร · การ์ตูน", CREAM, 1.0)], size=0.4))))
    return P


def amulet_stall():
    table = (60, 30, 30)
    P = [centred(28, 12, 12, z=-2, paint=per_face(solid(table), north=label((120, 20, 20), [("พระเครื่อง · เครื่องราง", GOLD, 1.0)], bands=[(0.0, 0.1, GOLD), (0.9, 1, GOLD)], size=0.24), up=solid((150, 30, 30))))]
    # glass case with small amulets
    P.append(centred(22, 4, 8, y=12, z=-2, paint=per_face(grid_goods([GOLD, (200, 200, 210), (120, 80, 40), (250, 214, 60)], rows=1, cols=8, bg=(40, 20, 20), gap=0.35), up=grid_goods([GOLD, (230, 230, 240), (150, 110, 60)], rows=2, cols=6, bg=(60, 30, 30), gap=0.4))))
    # backboard with hanging amulets + lanterns
    P.append(centred(28, 26, 1.5, y=0, z=5, paint=per_face(solid((90, 20, 20)), north=grid_goods([GOLD, (230, 230, 240), (200, 60, 60)], rows=4, cols=7, bg=(110, 24, 24), gap=0.45))))
    for x in (-11, 11):
        P.append(centred(3, 4, 3, y=27, x=x, z=3, paint=per_face(solid((220, 40, 30)), up=solid(GOLD), down=solid(GOLD))))
    return P


def rule_board():
    wood, paper = (110, 74, 40), (236, 226, 196)
    rules = label(paper, [("กฎ", (160, 20, 20), 1.6), ("ข้อ 1 ......", (60, 30, 20), 0.8), ("ข้อ 2 ......", (60, 30, 20), 0.8), ("ข้อ 3 ......", (60, 30, 20), 0.8)],
                  size=0.12, top=0.45)
    return [centred(1.6, 20, 1.6, x=-7, paint=solid(wood)), centred(1.6, 20, 1.6, x=7, paint=solid(wood)),
            centred(17, 13, 1.2, y=12, paint=per_face(solid(wood), north=solid((90, 60, 32)))),
            centred(13, 11, 0.4, y=13, z=-0.8, paint=per_face(solid(paper), north=rules)),
            centred(18, 1.2, 2.4, y=25, paint=solid(shade(wood, 0.8)))]


def watcher_statue():
    stone, dark = (150, 150, 146), (110, 110, 106)
    face = label(stone, icon=lambda d, w, h: (d.rectangle([w * 0.05, h * 0.3, w * 0.95, h * 0.62], fill=dark + (255,))))
    return [centred(10, 3, 10, paint=solid(dark)),                                    # base
            centred(3.6, 12, 3.6, y=3, x=-2.1, paint=solid(stone)), centred(3.6, 12, 3.6, y=3, x=2.1, paint=solid(stone)),
            centred(8.4, 12, 4.2, y=15, paint=solid(stone)),
            centred(8, 8, 8, y=27, paint=per_face(solid(stone), north=face)),
            # arms raised, hands covering the face
            centred(3.2, 9, 3.2, y=21, x=-5.4, z=-2.2, paint=solid(stone)), centred(3.2, 9, 3.2, y=21, x=5.4, z=-2.2, paint=solid(stone)),
            centred(7.6, 3.4, 1.6, y=29.4, z=-4.6, paint=solid(shade(stone, 0.92)))]


def haunted_speaker():
    body = (110, 70, 40)
    front = label(body, icon=lambda d, w, h: (d.ellipse([w * 0.08, h * 0.2, w * 0.5, h * 0.8], fill=(40, 30, 24, 255)),
                                              d.rectangle([w * 0.58, h * 0.25, w * 0.92, h * 0.45], fill=(230, 200, 120, 255)),
                                              d.ellipse([w * 0.62, h * 0.55, w * 0.74, h * 0.72], fill=(200, 180, 150, 255)),
                                              d.ellipse([w * 0.78, h * 0.55, w * 0.9, h * 0.72], fill=(200, 180, 150, 255))))
    return [centred(10, 7, 5, paint=per_face(solid(body), north=front)),
            centred(0.4, 5, 0.4, y=7, x=3.5, paint=solid((180, 180, 180))),
            centred(6, 1, 1, y=7, paint=solid((60, 40, 24)))]


def _register():
    for b in BOOKS:
        data_extra.EXTRA.append(dict(key=b['key'], name=b['name'], short=b['short'], en=b['en'], kind="hand", use="none", model=b['model'],
                                     group="books", reusable=True, max_stack=16 if b['consumed'] else 1, price=b['price'],
                                     food=0, sat=0, thirst=0, heal=0, effects=[], cure=[],
                                     desc=f"{b['desc']} §7(อ่านจบ: สติ {'+' if b['sanity'] > 0 else ''}{b['sanity']}"
                                          f"{', คูลดาวน์ ' + str(b['cooldown']) + ' นาที' if b['cooldown'] else ''})"))
    for a in AMULETS:
        data_extra.EXTRA.append(dict(key=a['key'], name=a['name'], short=a['short'], en=a['en'], kind="hand", use="none", icon2d=a['icon'],
                                     group="amulets", reusable=True, max_stack=1, price=a['price'], food=0, sat=0, thirst=0, heal=0,
                                     effects=[], cure=[], desc=f"{a['effect']} §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"))
    stands.STANDS["succubi:book_stall"] = dict(model=book_stall, collision=(2.0, 2.0), name="แผงหนังสือ", en="Book Stall")
    stands.STANDS["succubi:amulet_stall"] = dict(model=amulet_stall, collision=(2.0, 2.0), name="แผงพระเครื่อง", en="Amulet Stall")
    data_extra.SHOPS_EXTRA.append(dict(key="books", entity="succubi:book_stall", flag="§0§9§6§5", title="แผงหนังสือ", en="Book Stall",
                                       rows=5, coin_buttons=False, slots=[1, 5, 10, 20, 50, 100, 500, 1000],
                                       menu=[f"x:{b['key']}" for b in BOOKS],
                                       theme=dict(base=(170, 120, 70), dark=(110, 70, 36), accent=(240, 200, 90), glass=(34, 26, 18), cell=(60, 44, 30))))
    data_extra.SHOPS_EXTRA.append(dict(key="amulets", entity="succubi:amulet_stall", flag="§0§9§6§6", title="แผงพระเครื่อง", en="Amulet Stall",
                                       rows=5, coin_buttons=False, slots=[1, 5, 10, 20, 50, 100, 500, 1000],
                                       menu=[f"x:{a['key']}" for a in AMULETS],
                                       theme=dict(base=(120, 26, 26), dark=(70, 12, 12), accent=(232, 186, 60), glass=(30, 14, 12), cell=(56, 24, 22))))


_register()

HORROR_PROPS = {
    "succubi:rule_board": dict(model=rule_board, collision=(1.2, 1.9), name="ป้ายประกาศกฎ", en="Rule Board"),
    "succubi:watcher_statue": dict(model=watcher_statue, collision=(0.8, 2.3), name="รูปปั้นเฝ้ามอง", en="Watcher Statue"),
    "succubi:haunted_speaker": dict(model=haunted_speaker, collision=(0.7, 0.6), name="ลำโพงหลอน", en="Haunted Speaker"),
}


def wand_icon():
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([(60, 220), (190, 60)], fill=(40, 30, 30, 255), width=18)
    d.ellipse([168, 30, 224, 86], fill=(200, 20, 30, 255), outline=(250, 200, 80, 255), width=6)
    d.line([(90, 200), (70, 180)], fill=(250, 200, 80, 255), width=8)
    return im.resize((64, 64), Image.LANCZOS)


def bell_icon():
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.pieslice([56, 40, 200, 220], 180, 360, fill=(150, 120, 60, 255))
    d.rectangle([56, 128, 200, 190], fill=(150, 120, 60, 255))
    d.rectangle([40, 186, 216, 204], fill=(120, 94, 44, 255))
    d.ellipse([114, 200, 142, 228], fill=(80, 60, 30, 255))
    d.rectangle([118, 20, 138, 46], fill=(120, 94, 44, 255))
    return im.resize((64, 64), Image.LANCZOS)
