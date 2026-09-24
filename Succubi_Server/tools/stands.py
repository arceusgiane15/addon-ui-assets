"""Shop furniture models (units = 1/16 block, front = -z, floor at y=0)."""
from boxkit import solid, vgrad, label, cross, stripes, per_face, grid_goods, shade, dots
from data_extra import WHITE, BLACK, GREEN, DGREEN, RED, BLUE, ORANGE, YELLOW, S_OR, S_GR, S_RD, box, centred

GOODS_SNACK = [(230, 60, 50), (250, 200, 40), (40, 120, 200), (240, 130, 40), (60, 170, 80), (150, 60, 160), (230, 230, 230), (200, 40, 90)]
GOODS_DRINK = [(200, 30, 40), (30, 80, 190), (240, 140, 30), (60, 180, 80), (230, 230, 240), (120, 40, 20), (40, 170, 220), (20, 20, 20)]
GOODS_MED = [(250, 250, 250), (60, 130, 220), (230, 70, 70), (0, 160, 100), (250, 190, 40), (240, 140, 180)]


def store_header(text, w_px=None):
    return label((250, 250, 250), [(text, S_GR, 1.0)], bands=[(0.0, 0.2, S_OR), (0.2, 0.34, S_GR), (0.34, 0.44, S_RD)], size=0.34, top=0.72)


def pharmacy_stall():
    wood, white = (190, 150, 110), (246, 248, 246)
    P = []
    # counter
    P.append(centred(30, 14, 10, z=-4, paint=per_face(solid(white), north=label(white, [("ร้านขายยา", DGREEN, 1.0)], bands=[(0.0, 0.14, GREEN), (0.86, 1, GREEN)],
                                                                                  icon=cross(GREEN, cx=0.08, cy=0.5, r=0.2), size=0.26), up=solid((210, 230, 220)))))
    # glass display box on the counter with little boxes inside
    P.append(centred(22, 5, 6, y=14, z=-4, paint=per_face(grid_goods(GOODS_MED, rows=1, cols=8, bg=(200, 225, 230)), up=solid((200, 230, 235)))))
    # back shelf unit with medicine rows
    P.append(centred(30, 32, 4, z=7, paint=per_face(solid(white), north=grid_goods(GOODS_MED, rows=5, cols=9, bg=(235, 240, 238)))))
    # posts + canopy + sign
    for x in (-14.5, 14.5):
        P.append(centred(1.4, 40, 1.4, x=x, z=-9, paint=solid((230, 230, 230))))
    P.append(centred(33, 1.2, 22, y=40, z=-1, paint=per_face(stripes([GREEN, white], vertical=True, count=10), down=solid(white))))
    P.append(centred(26, 7, 1, y=41.2, z=-11, paint=per_face(solid(GREEN), north=label(GREEN, [("ขายยา · เวชภัณฑ์", WHITE, 1.0)], icon=cross(WHITE, cx=0.05, cy=0.5, r=0.3), size=0.36))))
    return P


def snack_shelf():
    frame, back = (236, 236, 232), (210, 214, 212)
    P = [centred(32, 3, 12, paint=solid((60, 60, 60))),                                   # kick plate
         centred(32, 30, 1.5, z=5.25, paint=per_face(solid(frame), north=solid(back))),    # back panel
         centred(1.5, 30, 12, x=-15.25, paint=solid(frame)), centred(1.5, 30, 12, x=15.25, paint=solid(frame))]
    for i, y in enumerate((3, 10, 17, 24)):
        P.append(centred(29, 0.8, 11, y=y, z=-0.25, paint=per_face(solid(frame), north=solid(S_OR if i % 2 == 0 else S_GR))))
        P.append(centred(28, 5.4, 6, y=y + 0.8, z=0.5, paint=per_face(solid((120, 120, 120)), north=grid_goods(GOODS_SNACK[i:] + GOODS_SNACK[:i], rows=1, cols=7, bg=(214, 214, 210)))))
    P.append(centred(32, 5, 2, y=30, z=4, paint=per_face(solid(frame), north=store_header("ขนม · ของว่าง"))))
    return P


def drink_fridge():
    white, inner = (240, 240, 240), (30, 38, 46)
    P = [centred(24, 3, 14, paint=solid((50, 50, 50))),
         centred(24, 34, 1.5, y=3, z=6.25, paint=per_face(solid(white), north=solid(inner))),
         centred(1.5, 34, 14, y=3, x=-11.25, paint=solid(white)), centred(1.5, 34, 14, y=3, x=11.25, paint=solid(white)),
         centred(24, 1.5, 14, y=37, paint=solid(white))]
    for i, y in enumerate((3.5, 12, 20.5, 29)):
        P.append(centred(21, 0.5, 12, y=y, paint=solid((200, 210, 220))))
        P.append(centred(20, 7.4, 4, y=y + 0.5, z=0.5, paint=per_face(solid((90, 110, 130)), north=grid_goods(GOODS_DRINK[i:] + GOODS_DRINK[:i], rows=1, cols=8, bg=inner, gap=0.25))))
    # door frames (glass doors: frame only)
    for x in (-10.5, 0, 10.5):
        P.append(centred(1, 34, 0.8, y=3, x=x, z=-6.6, paint=solid((200, 200, 205))))
    P.append(centred(22, 1, 0.8, y=3, z=-6.6, paint=solid((200, 200, 205))))
    P.append(centred(24, 6, 3, y=38.5, z=-5.5, paint=per_face(solid(white), north=store_header("เครื่องดื่มเย็น"))))
    return P


def hot_counter():
    white, steel = (240, 240, 238), (190, 194, 198)
    P = [centred(28, 16, 14, paint=per_face(solid(white), north=label(white, [("อาหารพร้อมทาน", S_RD, 1.0)], bands=[(0.0, 0.12, S_OR), (0.12, 0.2, S_GR), (0.2, 0.26, S_RD)], size=0.18, top=0.6))),
         centred(28, 1, 14, y=16, paint=solid(steel)),
         # roller grill with sausages
         centred(12, 2, 8, y=17, x=-7, paint=solid((60, 60, 60)))]
    for i in range(5):
        P.append(centred(10, 1.2, 1.2, y=19, x=-7, z=-3 + i * 1.5, paint=solid((170, 64, 40))))
    # bao / dim sum steamer display (glass box drawn as frame + trays)
    P.append(centred(12, 8, 9, y=17, x=7, paint=per_face(grid_goods([(250, 248, 240), (246, 196, 60)], rows=2, cols=4, bg=(90, 70, 50)), up=solid((220, 220, 225)))))
    P.append(centred(14, 1.5, 11, y=25, x=7, paint=solid(steel)))
    P.append(centred(28, 6, 2, y=30, z=5, paint=per_face(solid(white), north=store_header("ของร้อน · ไส้กรอก ซาลาเปา"))))
    for x in (-13.5, 13.5):
        P.append(centred(1, 13, 1, y=17, x=x, z=5, paint=solid(steel)))
    return P


STANDS = {
    "succubi:pharmacy_stall": dict(model=pharmacy_stall, collision=(2.0, 2.6), name="แผงขายยา", en="Pharmacy Stall"),
    "succubi:store_snack_shelf": dict(model=snack_shelf, collision=(2.0, 2.2), name="ชั้นวางขนม (ร้านสะดวกซื้อ)", en="Store Snack Shelf"),
    "succubi:store_drink_fridge": dict(model=drink_fridge, collision=(1.5, 2.8), name="ตู้แช่เครื่องดื่ม (ร้านสะดวกซื้อ)", en="Store Drink Fridge"),
    "succubi:store_hot_counter": dict(model=hot_counter, collision=(1.8, 2.2), name="เคาน์เตอร์อาหารพร้อมทาน (ร้านสะดวกซื้อ)", en="Store Hot Food Counter"),
}
