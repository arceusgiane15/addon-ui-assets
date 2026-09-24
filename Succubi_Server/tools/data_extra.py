"""Pharmacy + convenience-store goods: models (built from boxes) and what they do.
Units = 1/16 block, model upright on y=0, centred on x/z, front = -z."""
from boxkit import solid, vgrad, label, cross, dots, stripes, per_face, grid_goods, shade

WHITE, BLACK = (246, 246, 244), (26, 26, 28)
GREEN, DGREEN = (0, 150, 90), (0, 96, 60)
RED, BLUE, ORANGE, YELLOW = (214, 36, 40), (30, 90, 190), (240, 120, 30), (250, 206, 40)
S_OR, S_GR, S_RD = (241, 107, 34), (0, 128, 84), (228, 30, 42)   # convenience store stripes


def box(o, s, paint, **kw):
    d = dict(o=o, s=s, paint=paint); d.update(kw); return d


def centred(w, h, d, y=0, paint=None, x=0, z=0, **kw):
    return box([x - w / 2, y, z - d / 2], [w, h, d], paint, **kw)


def side_label(front, side=None, top=None, bottom=None):
    side = side or front
    return per_face(side, north=front, south=side, up=top or side, down=bottom or side)


# ------------------------------------------------------------------ pharmacy
def blister():
    front = label(WHITE, [("พาราเซตามอล", BLUE, 1.0), ("500 mg", RED, 0.9)], bands=[(0.78, 1, BLUE)], size=0.13, top=0.42)
    back = label((200, 204, 210), icon=dots([(235, 235, 235)], n=5, cy=0.5, r=0.08))
    return [centred(4.5, 6.5, 0.6, paint=per_face(solid((210, 214, 220)), north=front, south=back))]


def bottle(w, h, body, cap, lab, cap_h=1.2, neck=0.6, side=None):
    return [centred(w, h, w, paint=side_label(lab, side=side or solid(body), top=solid(body), bottom=solid(body))),
            centred(w * 0.55, neck, w * 0.55, y=h, paint=solid(shade(body, 0.9))),
            centred(w * 0.62, cap_h, w * 0.62, y=h + neck, paint=solid(cap))]


def cough_syrup():
    lab = label((60, 30, 18), [("ยาแก้ไอ", WHITE, 1.0), ("น้ำดำ", YELLOW, 1.0)], bands=[(0.3, 0.72, (150, 30, 30))], size=0.14)
    return bottle(2.8, 6.0, (60, 30, 18), (230, 230, 230), lab, side=label((60, 30, 18), bands=[(0.3, 0.72, (150, 30, 30))]))


def inhaler():
    lab = label(WHITE, [("ยาดม", DGREEN, 1.0)], bands=[(0.0, 0.18, GREEN), (0.82, 1, GREEN)], size=0.2)
    return [centred(1.4, 4.4, 1.4, paint=side_label(lab, side=label(WHITE, bands=[(0.0, 0.18, GREEN), (0.82, 1, GREEN)]), top=solid(GREEN), bottom=solid(GREEN))),
            centred(0.9, 0.9, 0.9, y=4.4, paint=solid((250, 250, 250)))]


def balm():
    lid = label((250, 190, 30), icon=dots([ORANGE, BLACK], n=4, cy=0.5, r=0.1))
    side = label((30, 30, 30), [("ยาหม่อง", (250, 190, 30), 1.0)], size=0.4)
    return [centred(3.2, 1.3, 3.2, paint=side_label(side, side=solid((30, 30, 30)), bottom=solid(BLACK))),
            centred(3.4, 0.6, 3.4, y=1.3, paint=per_face(solid((250, 190, 30)), up=lid))]


def plaster():
    front = label((238, 206, 170), [("พลาสเตอร์", RED, 1.0)], icon=cross(RED, cx=0.5, cy=0.68, r=0.18), size=0.16, top=0.3)
    return [centred(4.6, 3.0, 1.6, paint=side_label(front, side=solid((238, 206, 170))))]


def ors():
    front = label(ORANGE, [("ORS", WHITE, 1.3), ("เกลือแร่", WHITE, 0.9)], bands=[(0.82, 1, (255, 170, 60))], size=0.17, top=0.42)
    return [centred(3.8, 5.2, 0.5, paint=side_label(front, side=solid(ORANGE)))]


def vitamin_c():
    lab = label(ORANGE, [("VIT C", WHITE, 1.1), ("1000", YELLOW, 0.9)], size=0.17)
    return bottle(3.0, 4.2, ORANGE, WHITE, lab, cap_h=1.0, neck=0.3, side=solid(ORANGE))


def motion():
    front = label((70, 150, 230), [("ยาแก้", WHITE, 1.0), ("เมารถ", WHITE, 1.0)], bands=[(0.8, 1, WHITE)], size=0.17, top=0.42)
    return [centred(3.2, 4.2, 1.3, paint=side_label(front, side=solid((70, 150, 230))))]


def antacid():
    lab = label(WHITE, [("ยาธาตุ", (220, 60, 110), 1.0), ("น้ำขาว", (220, 60, 110), 1.0)], bands=[(0.0, 0.14, (240, 120, 160))], size=0.15)
    return bottle(2.8, 5.6, (238, 238, 232), (240, 120, 160), lab, side=label(WHITE, bands=[(0.0, 0.14, (240, 120, 160))]))


# ------------------------------------------------------------------ convenience store
def peanuts():
    front = label((170, 40, 30), [("ถั่วลิสง", YELLOW, 1.0), ("อบเกลือ", WHITE, 0.9)], icon=dots([(200, 150, 90)], n=4, cy=0.8, r=0.07), size=0.16, top=0.38)
    return [centred(4.0, 5.4, 1.4, paint=side_label(front, side=solid((170, 40, 30)))),
            centred(4.0, 0.5, 0.5, y=5.4, paint=solid((150, 30, 24)))]


def milk():
    front = label(WHITE, [("นมจืด", BLUE, 1.0), ("UHT", BLUE, 0.8)], bands=[(0.0, 0.16, BLUE)],
                  icon=dots([BLACK], n=3, cy=0.82, r=0.07), size=0.16, top=0.5)
    return [centred(3.0, 5.0, 2.0, paint=side_label(front, side=label(WHITE, bands=[(0.0, 0.16, BLUE)], icon=dots([BLACK], n=2, cy=0.6, r=0.1)), top=solid(WHITE))),
            centred(0.4, 1.2, 0.4, y=5.0, x=0.8, paint=solid(WHITE))]


def m150():
    lab = label((90, 45, 15), [("M-150", YELLOW, 1.0)], bands=[(0.35, 0.7, (240, 200, 40))], fg=RED, size=0.17)
    lab = label((90, 45, 15), [("M-150", RED, 1.0)], bands=[(0.34, 0.68, (240, 200, 40))], size=0.16)
    return bottle(2.0, 4.6, (90, 45, 15), (240, 200, 40), lab, cap_h=0.7, neck=0.9, side=label((90, 45, 15), bands=[(0.34, 0.68, (240, 200, 40))]))


def onigiri(filling):
    rice, nori = (248, 248, 244), (22, 40, 30)
    parts = [centred(5.2 - i * 1.4, 1.4, 1.8, y=i * 1.4, paint=solid(rice)) for i in range(4)]
    parts.append(centred(2.0, 2.4, 1.9, y=0, paint=solid(nori)))
    parts.append(centred(1.2, 0.8, 1.95, y=3.4, paint=solid(filling)))
    return parts


def sandwich():
    bread, ham, cheese = (236, 206, 150), (236, 150, 150), (250, 214, 80)
    layers = []
    for i in range(4):
        w = 5.4 - i * 1.3
        layers += [centred(w, 0.5, 2.6, y=i * 1.4, paint=solid(bread)),
                   centred(w, 0.3, 2.6, y=i * 1.4 + 0.5, paint=solid(ham)),
                   centred(w, 0.3, 2.6, y=i * 1.4 + 0.8, paint=solid(cheese)),
                   centred(w, 0.3, 2.6, y=i * 1.4 + 1.1, paint=solid(bread))]
    return layers


def toastie():
    front = label((250, 250, 250), [("แซนด์วิชอบ", (230, 110, 30), 1.0), ("แฮมชีส", RED, 0.9)], bands=[(0.0, 0.14, S_OR), (0.86, 1, S_GR)],
                  icon=dots([(236, 190, 120)], n=2, cy=0.72, r=0.14), size=0.15, top=0.36)
    return [centred(5.2, 5.6, 1.1, paint=side_label(front, side=solid((250, 250, 250))))]


def dumplings():
    tray = (250, 250, 250); dim = (246, 196, 60)
    parts = [centred(5.6, 0.6, 4.0, paint=solid(tray))]
    for x in (-1.3, 1.3):
        for z in (-0.9, 0.9):
            parts.append(centred(1.9, 1.5, 1.6, y=0.6, x=x, z=z, paint=per_face(solid(dim), up=solid((250, 120, 60)))))
    return parts


def bao():
    dough = (250, 248, 240)
    return [centred(4.6, 1.2, 4.6, paint=solid(dough)), centred(4.0, 1.0, 4.0, y=1.2, paint=solid(dough)),
            centred(2.8, 0.8, 2.8, y=2.2, paint=solid(dough)), centred(1.2, 0.5, 1.2, y=3.0, paint=solid((200, 60, 60)))]


def sausage():
    meat = (170, 60, 40)
    return [centred(0.35, 3.0, 0.35, paint=solid((230, 210, 170))),
            centred(1.4, 7.0, 1.4, y=2.6, paint=per_face(vgrad((190, 72, 48), (140, 44, 30)), up=solid(meat), down=solid(meat)))]


def rice_box(top_paint):
    return [centred(7.2, 1.8, 5.2, paint=per_face(solid((24, 24, 26)), up=top_paint))]


def krapow_top(w, h, face):
    from PIL import Image, ImageDraw
    im = Image.new('RGBA', (w, h), (250, 250, 246, 255)); d = ImageDraw.Draw(im)
    d.rectangle([w * 0.5, 0, w, h], fill=(150, 90, 50, 255))
    for i in range(7):
        x = w * (0.55 + 0.06 * i); y = h * (0.2 + 0.09 * (i % 5))
        d.ellipse([x, y, x + w * 0.07, y + h * 0.1], fill=(40, 130, 40, 255))
    d.ellipse([w * 0.08, h * 0.2, w * 0.45, h * 0.8], fill=(255, 255, 255, 255))
    d.ellipse([w * 0.19, h * 0.35, w * 0.33, h * 0.62], fill=(250, 170, 20, 255))
    return im


def garlic_top(w, h, face):
    from PIL import Image, ImageDraw
    im = Image.new('RGBA', (w, h), (250, 250, 246, 255)); d = ImageDraw.Draw(im)
    for i in range(5):
        d.rectangle([w * (0.5 + 0.09 * i), h * 0.15, w * (0.57 + 0.09 * i), h * 0.85], fill=(200, 120, 60, 255))
    for i in range(12):
        x = w * (0.52 + 0.035 * i); d.ellipse([x, h * (0.1 + 0.06 * (i % 6)), x + 3, h * (0.1 + 0.06 * (i % 6)) + 3], fill=(250, 220, 150, 255))
    d.rectangle([w * 0.08, h * 0.6, w * 0.4, h * 0.85], fill=(60, 150, 60, 255))
    return im


def boiled_eggs():
    return [centred(4.6, 0.6, 2.8, paint=solid((230, 230, 222))),
            centred(1.8, 2.2, 1.8, y=0.6, x=-1.1, paint=solid((250, 248, 240))),
            centred(1.8, 2.2, 1.8, y=0.6, x=1.1, paint=solid((250, 248, 240)))]


def teddy_model():
    fur, dark, snout = (170, 110, 60), (120, 74, 36), (230, 200, 160)
    face = label(fur, icon=lambda d, w, h: (d.ellipse([w * 0.22, h * 0.3, w * 0.36, h * 0.44], fill=(20, 20, 20, 255)),
                                            d.ellipse([w * 0.64, h * 0.3, w * 0.78, h * 0.44], fill=(20, 20, 20, 255))))
    belly = label(fur, icon=lambda d, w, h: d.ellipse([w * 0.2, h * 0.15, w * 0.8, h * 0.85], fill=snout + (255,)))
    P = [centred(4.2, 4.6, 3.2, y=0.8, paint=per_face(solid(fur), north=belly)),       # body
         centred(4.0, 3.6, 3.4, y=5.4, paint=per_face(solid(fur), north=face)),          # head
         centred(1.6, 1.0, 0.8, y=5.9, z=-2.0, paint=per_face(solid(snout), north=label(snout, icon=lambda d, w, h: d.ellipse([w * 0.3, h * 0.1, w * 0.7, h * 0.5], fill=(30, 20, 20, 255))))),
         centred(1.2, 1.2, 0.8, y=8.8, x=-1.6, paint=solid(dark)), centred(1.2, 1.2, 0.8, y=8.8, x=1.6, paint=solid(dark)),  # ears
         centred(1.3, 1.6, 1.6, y=0.0, x=-1.3, z=-0.6, paint=solid(dark)), centred(1.3, 1.6, 1.6, y=0.0, x=1.3, z=-0.6, paint=solid(dark)),  # legs
         centred(1.2, 3.0, 1.4, y=2.4, x=-2.7, paint=solid(fur)), centred(1.2, 3.0, 1.4, y=2.4, x=2.7, paint=solid(fur)),  # arms
         centred(3.0, 0.6, 3.3, y=5.0, paint=solid((200, 40, 60)))]  # ribbon
    return P



# key, name, en, kind (pose), use, model fn, stats
EXTRA = [
    # --- pharmacy
    dict(key="med_paracetamol", name="พาราเซตามอล 500 มก. (1 แผง)", en="Paracetamol 500mg (1 strip)", kind="hand", use="eat", model=blister, group="medical",
         price=15, food=0, sat=0, thirst=0, heal=10, effects=[("regeneration", 20, 0)], cure=[], desc="ลดไข้ แก้ปวด ฟื้นเลือดทันที"),
    dict(key="med_cough_syrup", name="ยาแก้ไอน้ำดำ", en="Brown Mixture Cough Syrup", kind="hand", use="drink", model=cough_syrup, group="medical",
         price=45, food=0, sat=0, thirst=2, heal=0, effects=[("regeneration", 15, 0)], cure=["weakness", "mining_fatigue"], desc="ชุ่มคอ หายอ่อนแรง"),
    dict(key="med_inhaler", name="ยาดม", en="Herbal Inhaler", kind="hand", use="eat", model=inhaler, group="medical",
         price=25, food=0, sat=0, thirst=0, heal=0, effects=[("night_vision", 60, 0)], cure=["nausea", "blindness", "darkness"], desc="สูดแล้วหายมึน ตาสว่าง"),
    dict(key="med_balm", name="ยาหม่อง", en="Herbal Balm", kind="hand", use="eat", model=balm, group="medical",
         price=35, food=0, sat=0, thirst=0, heal=0, effects=[("resistance", 30, 0)], cure=["slowness"], desc="ทาแล้วคลายเส้น ตัวเบา"),
    dict(key="med_plaster", name="พลาสเตอร์ปิดแผล (กล่อง)", en="Plasters (box)", kind="hand", use="eat", model=plaster, group="medical",
         price=20, food=0, sat=0, thirst=0, heal=6, effects=[("regeneration", 5, 0)], cure=[], desc="ปิดแผลเล็ก ฟื้นเลือดเล็กน้อย"),
    dict(key="med_ors", name="เกลือแร่ ORS (ซอง)", en="ORS Rehydration Salts", kind="hand", use="drink", model=ors, group="medical",
         price=8, food=0, sat=0, thirst=8, heal=0, effects=[], cure=["weakness"], desc="ชงน้ำดื่ม แก้ขาดน้ำ"),
    dict(key="med_vitamin_c", name="วิตามินซี 1000 มก.", en="Vitamin C 1000mg", kind="hand", use="eat", model=vitamin_c, group="medical",
         price=60, food=0, sat=0, thirst=0, heal=0, effects=[("absorption", 120, 0), ("regeneration", 10, 0)], cure=[], desc="เสริมภูมิ ร่างกายแข็งแรง"),
    dict(key="med_motion", name="ยาแก้เมารถ", en="Motion Sickness Pills", kind="hand", use="eat", model=motion, group="medical",
         price=20, food=0, sat=0, thirst=0, heal=0, effects=[], cure=["nausea", "darkness"], desc="หายเวียนหัว คลื่นไส้"),
    dict(key="med_antacid", name="ยาธาตุน้ำขาว", en="White Antacid Mixture", kind="hand", use="drink", model=antacid, group="medical",
         price=55, food=0, sat=0, thirst=1, heal=0, effects=[("regeneration", 5, 0)], cure=["poison", "hunger", "nausea"], desc="แก้ท้องอืด ถอนพิษอาหาร"),
    # --- convenience store: snacks / drinks
    dict(key="snack_peanuts", name="ถั่วลิสงอบเกลือ", en="Salted Roasted Peanuts", kind="hand", use="eat", model=peanuts, group="food",
         price=20, food=4, sat=0.5, thirst=-1, heal=0, effects=[], cure=[], desc="กรอบมัน เค็มนิดๆ"),
    dict(key="drink_milk", name="นมจืด UHT", en="Plain UHT Milk", kind="hand", use="drink", model=milk, group="food",
         price=14, food=2, sat=0.4, thirst=8, heal=0, effects=[], cure=["poison", "nausea", "weakness", "slowness"], desc="ดื่มแล้วล้างอาการแย่ๆ ออกหมด"),
    dict(key="drink_m150", name="เครื่องดื่มชูกำลัง M-150", en="M-150 Energy Drink", kind="hand", use="drink", model=m150, group="food",
         price=12, food=0, sat=0, thirst=5, heal=0, effects=[("haste", 60, 0), ("speed", 20, 0)], cure=[], desc="ขวดเล็ก พลังเต็ม"),
    # --- convenience store: ready meals
    dict(key="onigiri_tuna", name="ข้าวปั้นทูน่ามายองเนส", en="Tuna Mayo Onigiri", kind="hand", use="eat", model=lambda: onigiri((240, 230, 200)), group="food",
         price=25, food=5, sat=0.6, thirst=0, heal=0, effects=[], cure=[], desc="ข้าวญี่ปุ่นห่อสาหร่าย ไส้ทูน่า"),
    dict(key="onigiri_salmon", name="ข้าวปั้นแซลมอน", en="Salmon Onigiri", kind="hand", use="eat", model=lambda: onigiri((250, 130, 90)), group="food",
         price=35, food=6, sat=0.6, thirst=0, heal=0, effects=[("regeneration", 5, 0)], cure=[], desc="แซลมอนย่างชิ้นโต"),
    dict(key="sandwich_ham", name="แซนด์วิชแฮมชีส", en="Ham & Cheese Sandwich", kind="hand", use="eat", model=sandwich, group="food",
         price=29, food=5, sat=0.6, thirst=0, heal=0, effects=[], cure=[], desc="ขนมปังนุ่ม แฮม ชีส"),
    dict(key="toastie_ham", name="แซนด์วิชอบ แฮมชีส", en="Toasted Ham & Cheese", kind="hand", use="eat", model=toastie, group="food",
         price=39, food=7, sat=0.7, thirst=0, heal=0, effects=[("resistance", 20, 0)], cure=[], desc="อบร้อนๆ ชีสยืด"),
    dict(key="dim_sum", name="ขนมจีบกุ้ง (4 ชิ้น)", en="Shrimp Shumai (4 pcs)", kind="plate", use="eat", model=dumplings, group="food",
         price=25, food=5, sat=0.6, thirst=0, heal=0, effects=[], cure=[], desc="นึ่งร้อน ราดซีอิ๊วดำ"),
    dict(key="bao", name="ซาลาเปาหมูสับ", en="Minced Pork Bao", kind="hand", use="eat", model=bao, group="food",
         price=20, food=5, sat=0.7, thirst=0, heal=0, effects=[], cure=[], desc="แป้งนุ่ม ไส้แน่น"),
    dict(key="sausage", name="ไส้กรอกจัมโบ้", en="Jumbo Sausage", kind="hand", use="eat", model=sausage, group="food",
         price=35, food=6, sat=0.6, thirst=-1, heal=0, effects=[("strength", 20, 0)], cure=[], desc="ย่างร้อนๆ จากตู้"),
    dict(key="rice_krapow", name="ข้าวกะเพราไก่ไข่ดาว (กล่อง)", en="Basil Chicken Rice + Fried Egg", kind="plate", use="eat", model=lambda: rice_box(krapow_top), group="food",
         price=45, food=10, sat=0.8, thirst=-2, heal=0, effects=[("strength", 30, 0)], cure=[], desc="เวฟร้อน เผ็ดจัดจ้าน"),
    dict(key="rice_garlic_pork", name="ข้าวหมูทอดกระเทียม (กล่อง)", en="Garlic Pork Rice Box", kind="plate", use="eat", model=lambda: rice_box(garlic_top), group="food",
         price=49, food=10, sat=0.8, thirst=-1, heal=0, effects=[("resistance", 30, 0)], cure=[], desc="หมูทอดกรอบ กระเทียมเจียว"),
    dict(key="boiled_eggs", name="ไข่ต้ม (แพ็ค 2 ฟอง)", en="Boiled Eggs (2)", kind="hand", use="eat", model=boiled_eggs, group="food",
         price=12, food=4, sat=0.8, thirst=0, heal=0, effects=[], cure=[], desc="โปรตีนง่ายๆ อิ่มนาน"),
]

# chips flavours: recoloured Succubi chips bag (same model)
EXTRA.append(dict(key="teddy_bear", name="ตุ๊กตาหมีกอดคลายเครียด", en="Comfort Teddy Bear", kind="hand", use="none", model=teddy_model,
                  group="medical", reusable=True, price=99, food=0, sat=0, thirst=0, heal=0, effects=[], cure=[],
                  desc="คลิกขวากอดเพื่อเพิ่มสติ +12 (ทุก 90 วินาที) ใช้ได้ไม่จำกัด"))

CHIP_FLAVOURS = [
    dict(key="snack_chips_nori", name="มันฝรั่งทอดรสสาหร่าย", en="Nori Potato Chips", hue=100, price=20, food=4, sat=0.3, thirst=-1, desc="กรอบ หอมสาหร่าย"),
    dict(key="snack_chips_bbq", name="มันฝรั่งทอดรสบาร์บีคิว (ถุงใหญ่)", en="BBQ Potato Chips (big bag)", hue=8, price=33, food=6, sat=0.3, thirst=-2, desc="ถุงใหญ่ รสเข้มข้น"),
]

# vending items the store shelves also sell (same price as the machines)
V = lambda k: ("succubi:" + k)

SHOPS_EXTRA = [
    dict(key="pharmacy", entity="succubi:pharmacy_stall", flag="§0§9§6§1", title="แผงขายยา", en="Pharmacy Stall", rows=5, coin_buttons=False,
         slots=[1, 5, 10, 20, 50, 100, 500, 1000],
         menu=["x:med_paracetamol", "x:med_cough_syrup", "x:med_inhaler", "x:med_balm", "x:med_plaster", "x:med_ors",
               "x:med_vitamin_c", "x:med_motion", "x:med_antacid", "k:kotarus:bandage_blackpowder:35", "k:kotarus:syringe_blackpowder:150",
               "k:kotarus:medkit_blackpowder:590"],
         theme=dict(base=(232, 240, 234), dark=(0, 110, 70), accent=(0, 190, 110), glass=(18, 40, 30), cell=(30, 60, 46))),
    dict(key="seven_snack", entity="succubi:store_snack_shelf", flag="§0§9§6§2", title="ร้านสะดวกซื้อ · ชั้นขนม", en="Convenience Store · Snacks", rows=5, coin_buttons=False,
         slots=[1, 5, 10, 20, 50, 100, 500, 1000],
         menu=["v:snack_wafer", "v:snack_jelly", "v:snack_prawn_crackers", "v:snack_cream_bun", "v:snack_chips", "c:snack_chips_nori",
               "c:snack_chips_bbq", "v:snack_fish_strips", "v:snack_cookies", "v:snack_biscuit_sticks", "v:snack_seaweed", "v:snack_chocolate",
               "v:snack_chips_tube", "x:snack_peanuts", "x:teddy_bear"],
         theme=dict(base=(238, 238, 234), dark=(0, 120, 80), accent=(241, 107, 34), glass=(20, 30, 26), cell=(40, 48, 44))),
    dict(key="seven_drink", entity="succubi:store_drink_fridge", flag="§0§9§6§3", title="ร้านสะดวกซื้อ · ตู้แช่เครื่องดื่ม", en="Convenience Store · Drinks", rows=5, coin_buttons=False,
         slots=[1, 5, 10, 20, 50, 100, 500, 1000],
         menu=["v:drink_water_bottle", "x:drink_m150", "x:drink_milk", "v:drink_pepsi", "v:drink_fanta_orange", "v:drink_sprite",
               "v:drink_coca_cola", "v:drink_schweppes", "v:drink_boss_coffee", "v:drink_pocari_sweat", "v:drink_redbull",
               "v:drink_green_tea", "v:drink_monster_energy"],
         theme=dict(base=(238, 238, 234), dark=(0, 120, 80), accent=(80, 170, 230), glass=(16, 26, 36), cell=(34, 44, 52))),
    dict(key="seven_hot", entity="succubi:store_hot_counter", flag="§0§9§6§4", title="ร้านสะดวกซื้อ · อาหารพร้อมทาน", en="Convenience Store · Ready Meals", rows=5, coin_buttons=False,
         slots=[1, 5, 10, 20, 50, 100, 500, 1000],
         menu=["x:onigiri_tuna", "x:onigiri_salmon", "x:sandwich_ham", "x:toastie_ham", "x:dim_sum", "x:bao", "x:sausage",
               "x:rice_krapow", "x:rice_garlic_pork", "x:boiled_eggs"],
         theme=dict(base=(238, 238, 234), dark=(0, 120, 80), accent=(228, 30, 42), glass=(30, 20, 18), cell=(50, 40, 36))),
]
