import { world, system, EquipmentSlot, ItemStack } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { addSanity, runEvent } from "./sanity.js";
import { enabled, isAdmin } from "./settings_store.js";
import { HOOKS } from "./hooks.js";

// Books: right-click to read page by page on a paper screen; finishing gives sanity (once per cooldown).
export const PAPER_FLAG = "§0§9§5§1"; // skin in RP ui/server_form.json
const BTN = "textures/ui/succubi_paper/";
export const BOOKS = {
  "succubi:book_newspaper": {
    "key": "book_newspaper",
    "name": "หนังสือพิมพ์รายวัน",
    "sanity": 3,
    "cooldown": 0,
    "consumed": true,
    "special": "news",
    "pages": []
  },
  "succubi:book_comic": {
    "key": "book_comic",
    "name": "การ์ตูนแก๊กขำกลิ้ง",
    "sanity": 10,
    "cooldown": 10,
    "consumed": false,
    "special": "",
    "pages": [
      "ลุงแดงซื้อตู้เย็นใหม่ แต่ลืมว่าบ้านไม่มีไฟฟ้า... ตอนนี้ใช้เป็นตู้เก็บรองเท้าแทน",
      "นักรบเอาเข็มฉีดยาไปแทงกล้วย แล้วบอกว่า 'ช่วยชีวิตมันไว้แล้ว!' ... กล้วยไม่ได้ป่วยครับ",
      "ผีบ้านร้างออกมาหลอก แต่เจอหนี้บัตรเครดิตของเจ้าของบ้าน ผีเลยร้องไห้กลับเข้าไปเอง"
    ]
  },
  "succubi:book_travel": {
    "key": "book_travel",
    "name": "นิตยสารเที่ยวทั่วไทย",
    "sanity": 8,
    "cooldown": 10,
    "consumed": false,
    "special": "",
    "pages": [
      "ทะเลอันดามันเช้านี้ใสจนเห็นปลาว่ายรอบเท้า เสียงคลื่นทำให้ลืมทุกเรื่อง",
      "ดอยอินทนนท์ ทะเลหมอกลอยต่ำ กาแฟร้อนหนึ่งแก้วกับลมหนาว",
      "ตลาดน้ำยามเย็น ก๋วยเตี๋ยวเรือชามเล็ก กับแสงไฟตะเกียงริมคลอง"
    ]
  },
  "succubi:book_romance": {
    "key": "book_romance",
    "name": "นิยายรัก 'ใต้แสงจันทร์'",
    "sanity": 15,
    "cooldown": 20,
    "consumed": false,
    "special": "",
    "pages": [
      "คืนนั้นดวงจันทร์เต็มดวง เธอยื่นร่มให้เขาทั้งที่ฝนไม่ได้ตก...",
      "'ถ้าวันหนึ่งฉันหลงทาง เธอจะตามหาไหม' — 'ฉันจะเป็นแสงไฟให้เธอเดินกลับมา'",
      "ตอนจบ ทั้งคู่นั่งดูพระจันทร์ด้วยกัน และไม่มีใครกลัวความมืดอีกเลย"
    ]
  },
  "succubi:book_mystery": {
    "key": "book_mystery",
    "name": "นิยายสืบสวน 'คดีบ้านร้าง'",
    "sanity": 15,
    "cooldown": 20,
    "consumed": false,
    "special": "",
    "pages": [
      "บ้านร้างหลังนั้นมีรอยเท้าเปียกทั้งที่ฝนไม่ตกมาสามวัน นักสืบก้มลงดู...",
      "เบาะแสชิ้นสุดท้ายคือกุญแจที่ไขได้ทุกประตู ยกเว้นประตูห้องใต้ดิน",
      "คนร้ายคือ... ภารโรง! คดีปิด นักสืบกลับบ้านไปกินข้าวไข่เจียวสูตรผู้บัญชาการ"
    ]
  },
  "succubi:book_dharma": {
    "key": "book_dharma",
    "name": "หนังสือธรรมะ 'ใจสงบ'",
    "sanity": 20,
    "cooldown": 30,
    "consumed": false,
    "special": "calm",
    "pages": [
      "ความกลัวเกิดจากใจ เมื่อรู้ทันใจ ความกลัวก็เบาบางลง",
      "หายใจเข้า รู้ว่าหายใจเข้า หายใจออก รู้ว่าหายใจออก",
      "สิ่งที่มองไม่เห็นไม่อาจทำร้ายใจที่สงบได้ — ขออนุโมทนา"
    ]
  },
  "succubi:book_prayer": {
    "key": "book_prayer",
    "name": "หนังสือสวดมนต์",
    "sanity": 6,
    "cooldown": 10,
    "consumed": false,
    "special": "ward",
    "pages": [
      "อิติปิ โส ภะคะวา อะระหัง สัมมาสัมพุทโธ...",
      "สวากขาโต ภะคะวะตา ธัมโม สันทิฏฐิโก อะกาลิโก...",
      "ขอคุณพระคุ้มครอง ให้แคล้วคลาดจากสิ่งไม่ดีทั้งปวง สาธุ"
    ]
  },
  "succubi:book_coloring": {
    "key": "book_coloring",
    "name": "สมุดระบายสี + สีเทียน",
    "sanity": 8,
    "cooldown": 10,
    "consumed": false,
    "special": "",
    "pages": [
      "หน้า 1: รูปแมวนอนบนหมอน — คุณระบายสีส้มลงไปช้าๆ",
      "หน้า 2: รูปดอกบัวในบึง — สีชมพูอ่อนกับเขียวใบบัว",
      "หน้า 3: รูปบ้านหลังเล็กมีไฟเปิดอยู่ — อบอุ่นดีจัง"
    ]
  },
  "succubi:book_survival": {
    "key": "book_survival",
    "name": "คู่มือเอาชีวิตรอดฉบับพกพา",
    "sanity": 5,
    "cooldown": 5,
    "consumed": false,
    "special": "guide",
    "pages": [
      "สติ (วงสมอง): กินของอร่อย นอนหลับ อ่านหนังสือ กอดตุ๊กตา = สติเพิ่ม | โดนตี อยู่ใกล้มอนสเตอร์ เจอเรื่องแปลก = สติลด",
      "น้ำ (วงหยดน้ำ): ของเผ็ด/เค็มทำให้คอแห้ง ซุปกับเครื่องดื่มช่วยได้ | ร้านยามี ORS กับยาแก้ไอ",
      "เครื่องราง: เปิดกระเป๋าตังค์ > เครื่องราง ใส่ได้ 4 ชิ้น | ถ้าเห็นป้ายกฎ... ทำตามกฎเสมอ"
    ]
  },
  "succubi:book_ghost": {
    "key": "book_ghost",
    "name": "หนังสือเล่มดำ 'เรื่องเล่าต้องห้าม'",
    "sanity": -10,
    "cooldown": 15,
    "consumed": false,
    "special": "cursed",
    "pages": [
      "มีคนเขียนไว้ด้วยลายมือสั่นเทา: 'ถ้าได้ยินเสียงเคาะสามครั้ง อย่าเปิดประตู'",
      "'ถ้าเห็นรูปปั้นขยับ อย่ากะพริบตา อย่าหันหลัง'",
      "หน้าสุดท้ายว่างเปล่า... แต่กระดาษชื้นเหมือนเพิ่งมีคนแตะ"
    ]
  }
};
const NEWS = [
  "ด่วน! พบเงาดำยืนมองชาวบ้านกลางทุ่ง ตำรวจยังไม่พบเบาะแส",
  "ถังไก่ทอดยายน้อยขายหมดเกลี้ยงตั้งแต่เช้า ลูกค้าต่อคิวยาวถึงร้านยา",
  "{who} ถูกลือว่าเห็นรูปปั้นขยับเอง เจ้าตัวปฏิเสธ 'ผมไม่ได้มองมันเลย'",
  "หมอเตือน: สติต่ำอันตราย ควรอ่านหนังสือ กินของอร่อย และนอนให้พอ",
  "ร้านน้ำชาฮารุโตะยืนยัน 'เพลงในร้านไม่ได้เปิดเองตอนตีสาม'",
  "นักวิชาการชี้ คืนพระจันทร์เลือดมาเฉลี่ยสัปดาห์ละครั้ง แนะนำให้อยู่เป็นกลุ่ม",
  "{who} ซื้อเครื่องรางนางกวักไป ร้านค้าทั่วเซิร์ฟบ่นขายได้กำไรน้อยลง",
  "พบป้ายประกาศกฎประหลาดหน้าอาคารร้าง เขียนว่า 'ห้ามวิ่ง'",
  "ตลาดนัดสัปดาห์นี้ ราคาเกลือแร่ ORS ยังคงที่ 8 บาท",
  "ผลสำรวจ: ชาวเซิร์ฟ 9 ใน 10 คนเคยได้ยินเสียงเคาะประตูทั้งที่ไม่มีใคร",
  "{who} ได้รับรางวัลนักอ่านดีเด่นประจำเดือน (ข่าวลือ)",
  "ช่างตัดสินใจไม่ซ่อมประตูบ้านร้าง 'มันเปิดเองอยู่แล้ว'",
  "ราคาข้าวกะเพราไข่ดาวในร้านสะดวกซื้อยังคุ้มที่สุดในย่าน",
  "มีผู้พบเห็นค้างคาวบินออกมาจากความมืดเป็นฝูง ทั้งที่ไม่มีถ้ำ"
];

// Prayer book: the next strange event is cancelled
HOOKS.eventBlock.push((p) => {
  if (p.getDynamicProperty("succubi:ward") !== true) return false;
  p.setDynamicProperty("succubi:ward", false);
  p.onScreenDisplay.setActionBar("§eบทสวดมนต์คุ้มครองคุณจากสิ่งแปลกประหลาด");
  return true;
});

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

function newsPages() {
  const names = world.getAllPlayers().map((p) => p.name);
  const who = () => (names.length ? names[Math.floor(Math.random() * names.length)] : "ชาวบ้าน");
  const pick = () => NEWS[Math.floor(Math.random() * NEWS.length)].replace("{who}", who());
  return [pick(), pick(), pick()];
}

export async function readBook(player, id, page = 0, pages = undefined) {
  const book = BOOKS[id];
  if (!book) return;
  if (!pages) pages = book.special === "news" ? newsPages() : book.pages;
  const last = page >= pages.length - 1;
  const form = new ActionFormData()
    .title(`§l${book.name}${PAPER_FLAG}`)
    .body(`${pages[page]}\n\n§r§l— หน้า ${page + 1}/${pages.length} —`)
    .button(last ? "§2อ่านจบ" : "§0หน้าถัดไป »", `${BTN}${last ? "btn_done" : "btn_next"}`)
    .button("§4ปิดหนังสือ", `${BTN}btn_close`);
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 1) return;
  if (!last) return readBook(player, id, page + 1, pages);
  finish(player, id, book);
}

function removeFromHand(player, id) {
  const eq = player.getComponent("minecraft:equippable");
  const held = eq?.getEquipment(EquipmentSlot.Mainhand);
  if (held?.typeId !== id) return;
  if (held.amount > 1) {
    held.amount -= 1;
    eq.setEquipment(EquipmentSlot.Mainhand, held);
  } else eq.setEquipment(EquipmentSlot.Mainhand, undefined);
}

function finish(player, id, book) {
  const prop = `succubi:read_${book.key}`;
  const last = Number(player.getDynamicProperty(prop)) || 0;
  const wait = book.cooldown * 60000 - (Date.now() - last);
  if (book.consumed) removeFromHand(player, id);
  if (wait > 0) {
    player.onScreenDisplay.setActionBar(`§7เพิ่งอ่านเล่มนี้ไป อีก ${Math.ceil(wait / 60000)} นาทีถึงจะรู้สึกดีขึ้นอีก`);
    return;
  }
  player.setDynamicProperty(prop, Date.now());
  if (enabled("sanity")) addSanity(player, book.sanity);
  player.playSound(book.sanity >= 0 ? "random.orb" : "mob.elderguardian.curse");
  let msg = book.sanity >= 0 ? `§aอ่านจบ รู้สึกดีขึ้น (สติ +${book.sanity})` : `§4อ่านจบ... มีบางอย่างผิดปกติ (สติ ${book.sanity})`;
  if (book.special === "calm") {
    player.setDynamicProperty("succubi:calm_until", Date.now() + 30 * 60000);
    msg += " §eไม่หวั่นคำสาป 30 นาที";
  } else if (book.special === "ward") {
    player.setDynamicProperty("succubi:ward", true);
    msg += " §eคุ้มครองเรื่องแปลกครั้งถัดไป";
  } else if (book.special === "cursed") {
    player.addEffect("night_vision", 20 * 60, { amplifier: 0, showParticles: false });
    system.runTimeout(() => {
      try {
        if (enabled("sanity") && enabled("events")) runEvent(player);
      } catch (e) {}
    }, 40);
  }
  player.onScreenDisplay.setActionBar(msg);
}

// ---------------------------------------------------------------- the admin's writable book (สมุดเขียนเอง)
// The item carries an id (item dynamic property); the text lives in a world property under that id, so every copy
// of a book shows the same, latest text. Blank book: admins write it; players are told it is empty.
export const CUSTOM_BOOK = "succubi:book_custom";
const CB_ID = "succubi:book_id";
const cbKey = (id) => `succubi:cbook_${id}`;
const MAX_PAGES = 30;
const PAGE_CHARS = 1500;
const SANITY_CHOICES = [0, 3, 5, 10, 15, -5, -10];

function loadCustom(id) {
  try {
    const v = JSON.parse(world.getDynamicProperty(cbKey(id)) ?? "null");
    if (v && Array.isArray(v.pages)) return v;
  } catch (e) {}
  return undefined;
}

// "//" in the text = new line; long pages are split so they fit on the paper (about 400 letters each)
export function bookSheets(pages) {
  const out = [];
  for (const raw of pages) {
    let text = String(raw ?? "").split("//").map((x) => x.trim()).join("\n");
    while (text.length > 420) {
      let cutAt = Math.max(text.lastIndexOf("\n", 420), text.lastIndexOf(" ", 420));
      if (cutAt < 200) cutAt = 420;
      out.push(text.slice(0, cutAt).trim());
      text = text.slice(cutAt).trim();
    }
    if (text) out.push(text);
  }
  return out.length ? out : ["§7(หน้าว่าง)"];
}

async function readCustom(player, book, id, page = 0, sheets = undefined) {
  sheets = sheets ?? bookSheets(book.pages);
  const last = page >= sheets.length - 1;
  const form = new ActionFormData()
    .title(`§l${book.title}${PAPER_FLAG}`)
    .body(`${page === 0 && book.author ? `§8โดย ${book.author}\n\n` : ""}§0${sheets[page]}\n\n§r§8— หน้า ${page + 1}/${sheets.length} —`)
    .button(last ? "§2อ่านจบ" : "§0หน้าถัดไป »", `${BTN}${last ? "btn_done" : "btn_next"}`)
    .button("§4ปิดหนังสือ", `${BTN}btn_close`);
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 1) return;
  if (!last) return readCustom(player, book, id, page + 1, sheets);
  if (!id || !book.sanity) return;
  const prop = `succubi:read_c_${id}`;
  if (Date.now() - (Number(player.getDynamicProperty(prop)) || 0) < 10 * 60000) return;
  player.setDynamicProperty(prop, Date.now());
  if (enabled("sanity")) addSanity(player, book.sanity);
  player.onScreenDisplay.setActionBar(book.sanity > 0 ? `§aอ่านจบ รู้สึกดีขึ้น (สติ +${book.sanity})` : `§4อ่านจบ... ใจคอไม่ดี (สติ ${book.sanity})`);
}

function heldBook(player) {
  const eq = player.getComponent("minecraft:equippable");
  const item = eq?.getEquipment(EquipmentSlot.Mainhand);
  return item?.typeId === CUSTOM_BOOK ? { eq, item } : undefined;
}

function stampItem(item, id, book) {
  item.setDynamicProperty(CB_ID, id);
  item.nameTag = `§r§f${book.title}`;
  item.setLore([book.author ? `§7โดย ${book.author}` : "§7สมุดเขียนเอง", `§8${book.pages.length} หน้า`]);
  return item;
}

async function typeBox(player, title, hint, value) {
  const r = await show(new ModalFormData().title(`§l${title}`).textField(title, hint, String(value ?? "")), player);
  if (!r || r.canceled) return undefined;
  return String(r.formValues?.[0] ?? "").slice(0, PAGE_CHARS);
}

async function editCustom(player, id, draft, note = "") {
  const b = draft;
  const sanityText = b.sanity ? `${b.sanity > 0 ? "+" : ""}${b.sanity}` : "ไม่มี";
  const form = new ActionFormData()
    .title("§lเขียนสมุด")
    .body(`§fแตะแถวเพื่อแก้ แล้วกด §aบันทึก§f\n§7${b.pages.length}/${MAX_PAGES} หน้า · ขึ้นบรรทัดใหม่พิมพ์ // · หน้ายาวจะแบ่งหน้าให้เอง${note ? `\n${note}` : ""}`);
  const rows = [["title", `§lชื่อหนังสือ\n§f${b.title}`], ["author", `§lผู้เขียน\n${b.author ? `§f${b.author}` : "§7(ไม่ระบุ)"}`]];
  b.pages.forEach((pg, i) => rows.push([i, `§lหน้า ${i + 1}\n§7${pg.replace(/\/\//g, " ").slice(0, 30)}${pg.length > 30 ? "..." : ""}`]));
  if (b.pages.length < MAX_PAGES) rows.push(["add", "§l§a+ เพิ่มหน้า"]);
  rows.push(["sanity", `§lอ่านจบแล้วสติ: §e${sanityText}\n§7นับได้ทุก 10 นาที`], ["preview", "§lลองอ่าน"], ["save", "§l§aบันทึก"], ["cancel", "§7ยกเลิก"]);
  rows.forEach(([, t]) => form.button(t));
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const key = rows[r.selection][0];
  if (key === "cancel") return;
  if (key === "save") return saveCustom(player, id, b);
  if (key === "preview") await readCustom(player, b, undefined);
  else if (key === "title") {
    const v = await typeBox(player, "ชื่อหนังสือ", "เช่น บันทึกของผู้รอดชีวิต", b.title);
    if (v !== undefined && v.trim()) b.title = v.trim().slice(0, 60);
  } else if (key === "author") {
    const v = await typeBox(player, "ผู้เขียน", "เว้นว่างได้", b.author);
    if (v !== undefined) b.author = v.trim().slice(0, 40);
  } else if (key === "add") {
    const v = await typeBox(player, `หน้า ${b.pages.length + 1}`, "พิมพ์เนื้อหา ขึ้นบรรทัดใหม่พิมพ์ //", "");
    if (v && v.trim()) b.pages.push(v.trim());
  } else if (key === "sanity") {
    const m = new ModalFormData().title("§lผลเมื่ออ่านจบ")
      .dropdown("สติ", SANITY_CHOICES.map((v) => (v ? `${v > 0 ? "+" : ""}${v}` : "ไม่มีผล")), Math.max(0, SANITY_CHOICES.indexOf(b.sanity)));
    const a = await show(m, player);
    if (a && !a.canceled) b.sanity = SANITY_CHOICES[a.formValues[0]] ?? 0;
  } else if (typeof key === "number") {
    const m = new ActionFormData().title(`§lหน้า ${key + 1}`).body(`§f${b.pages[key].replace(/\/\//g, "\n")}`)
      .button("§lแก้ข้อความ").button("§lเลื่อนขึ้น").button("§lเลื่อนลง").button("§l§cลบหน้านี้").button("§7« กลับ");
    const a = await show(m, player);
    if (a && !a.canceled) {
      const i = key;
      if (a.selection === 0) {
        const v = await typeBox(player, `หน้า ${i + 1}`, "ขึ้นบรรทัดใหม่พิมพ์ //", b.pages[i]);
        if (v !== undefined && v.trim()) b.pages[i] = v.trim();
      } else if (a.selection === 1 && i > 0) [b.pages[i - 1], b.pages[i]] = [b.pages[i], b.pages[i - 1]];
      else if (a.selection === 2 && i < b.pages.length - 1) [b.pages[i + 1], b.pages[i]] = [b.pages[i], b.pages[i + 1]];
      else if (a.selection === 3) b.pages.splice(i, 1);
    }
  }
  return editCustom(player, id, b);
}

function saveCustom(player, id, b) {
  const held = heldBook(player);
  const bookId = id ?? `b${Date.now().toString(36)}${Math.floor(Math.random() * 1296).toString(36)}`;
  world.setDynamicProperty(cbKey(bookId), JSON.stringify({ title: b.title, author: b.author, pages: b.pages, sanity: b.sanity }));
  if (held && (held.item.getDynamicProperty(CB_ID) ?? bookId) === bookId) held.eq.setEquipment(EquipmentSlot.Mainhand, stampItem(held.item, bookId, b));
  player.sendMessage(`§a[สมุด] บันทึก "${b.title}" แล้ว (${b.pages.length} หน้า) ทุกเล่มที่เป็นเล่มเดียวกันจะเห็นข้อความใหม่`);
}

async function customMenu(player, id, book) {
  const form = new ActionFormData().title(`§l${book.title}`).body(`§7${book.pages.length} หน้า${book.author ? ` · โดย ${book.author}` : ""}\n§7แก้แล้วทุกเล่มที่คัดลอกไปจะเปลี่ยนตาม`)
    .button("§lอ่าน").button("§lแก้ไข").button("§lคัดลอกให้ตัวเอง 1 เล่ม\n§7ไว้แจกผู้เล่น").button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return readCustom(player, book, id);
  if (r.selection === 1) return editCustom(player, id, { ...book, pages: [...book.pages], sanity: book.sanity ?? 0 });
  if (r.selection === 2) {
    const copy = stampItem(new ItemStack(CUSTOM_BOOK, 1), id, book);
    const left = player.getComponent("minecraft:inventory")?.container?.addItem(copy);
    if (left) player.dimension.spawnItem(left, player.location);
    player.sendMessage("§a[สมุด] คัดลอกแล้ว 1 เล่ม");
  }
}

export function useCustomBook(player, item) {
  const id = item.getDynamicProperty(CB_ID);
  const book = typeof id === "string" ? loadCustom(id) : undefined;
  if (!book) {
    if (!isAdmin(player)) return player.onScreenDisplay.setActionBar("§7สมุดเล่มนี้ยังว่างอยู่...");
    return editCustom(player, undefined, { title: "สมุดไม่มีชื่อ", author: player.name, pages: [], sanity: 0 });
  }
  return isAdmin(player) ? customMenu(player, id, book) : readCustom(player, book, id);
}

export function initBooks() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId === CUSTOM_BOOK) {
      const player = event.source;
      const item = event.itemStack;
      system.run(() => {
        Promise.resolve(useCustomBook(player, item)).catch(() => {});
      });
      return;
    }
    if (!BOOKS[event.itemStack?.typeId]) return;
    const player = event.source;
    const id = event.itemStack.typeId;
    system.run(() => {
      readBook(player, id).catch(() => {});
    });
  });
}
