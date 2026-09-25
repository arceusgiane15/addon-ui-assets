import { SHOP_MENUS } from "./products.js";

// Kiosk shops: right-click = shop screen (same cash / change flow as the vending machines),
// sneak + right-click = dismantle (handled by the entity). The flag picks the skin in RP ui/server_form.json.
export const SHOPS = {
  "kiosk:somtum_kiosk": { flag: "§0§9§7§1", title: "ร้านส้มตำครกทอง", products: SHOP_MENUS.somtum, prefix: "somtum", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "kiosk:chicken_kiosk": { flag: "§0§9§7§2", title: "ร้านไก่ทอดสูตรยายน้อย", products: SHOP_MENUS.chicken, prefix: "chicken", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "kiosk:ramen_kiosk": { flag: "§0§9§7§3", title: "ร้านบะหมี่สูตรท่านฮารุโตะ", products: SHOP_MENUS.ramen, prefix: "ramen", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "kiosk:omelette_kiosk": { flag: "§0§9§7§4", title: "ร้านข้าวไข่เจียว สูตรผู้บัญชาการ", products: SHOP_MENUS.omelette, prefix: "omelette", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "kiosk:fried_insects_kiosk": { flag: "§0§9§7§5", title: "ร้านแมลงทอดสูตรท่านฮารุโตะ", products: SHOP_MENUS.fried_insects, prefix: "fried_insects", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "kiosk:haruto_tea_kiosk": { flag: "§0§9§7§6", title: "ร้านน้ำชาฮารุโตะ", products: SHOP_MENUS.haruto_tea, prefix: "haruto_tea", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] },
  "succubi:pharmacy_stall": { flag: "§0§9§6§1", title: "แผงขายยา", products: SHOP_MENUS.pharmacy, prefix: "pharmacy", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false },
  "succubi:store_snack_shelf": { flag: "§0§9§6§2", title: "ร้านสะดวกซื้อ · ชั้นขนม", products: SHOP_MENUS.seven_snack, prefix: "seven_snack", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false },
  "succubi:store_drink_fridge": { flag: "§0§9§6§3", title: "ร้านสะดวกซื้อ · ตู้แช่เครื่องดื่ม", products: SHOP_MENUS.seven_drink, prefix: "seven_drink", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false },
  "succubi:store_hot_counter": { flag: "§0§9§6§4", title: "ร้านสะดวกซื้อ · อาหารพร้อมทาน", products: SHOP_MENUS.seven_hot, prefix: "seven_hot", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false },
  "succubi:book_stall": { flag: "§0§9§6§5", title: "แผงหนังสือ", products: SHOP_MENUS.books, prefix: "books", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false },
  "succubi:amulet_stall": { flag: "§0§9§6§6", title: "แผงพระเครื่อง", products: SHOP_MENUS.amulets, prefix: "amulets", tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true, who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000], coinButtons: false }
};

// Stands built for this server turn to face whoever places them (the kiosks keep their own facing)
export const FACE_ON_PLACE = ["succubi:pharmacy_stall", "succubi:store_snack_shelf", "succubi:store_drink_fridge", "succubi:store_hot_counter", "succubi:book_stall", "succubi:amulet_stall"];
