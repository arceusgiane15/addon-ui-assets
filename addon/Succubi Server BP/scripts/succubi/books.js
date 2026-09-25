import { world, system, EquipmentSlot, ItemStack } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { addSanity, runEvent } from "./sanity.js";
import { enabled, isAdmin } from "./settings_store.js";
import { HOOKS } from "./hooks.js";

// Books: right-click to read page by page; finishing gives sanity (once per cooldown).
// Books open the book window (RP ui/succubi_paper.json book_panel, flag BOOK_FLAG): a leather-bound page, or a
// scorched one for the black book, or newsprint for the newspaper (THEME), with the book's own icon (ICON).
// Rule boards keep the plain paper window (PAPER_FLAG, used by horror.js).
export const PAPER_FLAG = "§0§9§5§1";
export const BOOK_FLAG = "§0§9§5§2";
const THEME = { cursed: "§8§8§1", news: "§8§8§2" };
const ICON = ["book_newspaper", "book_comic", "book_travel", "book_romance", "book_mystery", "book_dharma",
  "book_prayer", "book_coloring", "book_survival", "book_ghost", "book_custom"];
const iconFlag = (key) => `§6§6§${"0123456789a"[Math.max(0, ICON.indexOf(key))]}`;
const BTN = "textures/ui/succubi_paper/";

// Page text: "\n" = new line. A page holds about 12 lines on the book window.
export const BOOKS = {
  "succubi:book_newspaper": {
    key: "book_newspaper",
    name: "หนังสือพิมพ์รายวัน",
    sanity: 3,
    cooldown: 0,
    consumed: true,
    special: "news",
    pages: []
  },
  "succubi:book_comic": {
    key: "book_comic",
    name: "การ์ตูนแก๊กขำกลิ้ง",
    sanity: 10,
    cooldown: 10,
    consumed: false,
    special: "",
    pages: [
      "§lตอนที่ 1: ตู้เย็นของลุงแดง§r\n\nลุงแดงเก็บเงินอยู่สามเดือนเพื่อซื้อตู้เย็นสองประตูรุ่นใหม่ล่าสุด แบกขึ้นรถมาเองกับมือ ยกเข้าบ้านเองอีก เหงื่อท่วมตัว\n\nพอเสียบปลั๊กเสร็จ ลุงยืนรอให้ไฟเขียวติด... รอ... รอ... รอจนพระอาทิตย์ตก\n\nแล้วลุงก็นึกขึ้นได้ว่าบ้านยังไม่ได้ต่อไฟฟ้า\n\nทุกวันนี้ตู้เย็นใบนั้นยังอยู่ที่เดิม ข้างในมีรองเท้าแตะเรียงอย่างเป็นระเบียบ ลุงบอกทุกคนว่า 'ตู้รองเท้าที่เย็นที่สุดในหมู่บ้าน'",
      "§lตอนที่ 2: นักรบผู้กล้า§r\n\nนักรบหนุ่มเพิ่งได้เข็มฉีดยาอันแรกจากร้านขายยา เขาถือมันเหมือนดาบวิเศษ มองหาใครสักคนที่ต้องการความช่วยเหลือ\n\nเขาเห็นกล้วยหอมลูกหนึ่งมีจุดดำเต็มตัว 'เจ้าป่วยหนักแล้วสินะ!' เขาตะโกน แล้วปักเข็มลงไปอย่างกล้าหาญ\n\n'รอดแล้ว! ข้าช่วยชีวิตเจ้าไว้ได้!'\n\nแม่ค้าผลไม้ยืนมองอยู่นานมาก ก่อนจะพูดเบาๆ ว่า 'หนูจ๋า... กล้วยมันแค่สุกจ้ะ แล้วลูกนั้นยังไม่ได้จ่ายเงินนะ'",
      "§lตอนที่ 3: ผีบ้านร้างกับจดหมาย§r\n\nผีสาวในบ้านร้างหลังเก่าตั้งใจจะหลอกเจ้าของบ้านคนใหม่ให้หนีไปภายในคืนเดียว เธอซ้อมหัวเราะเสียงแหลมมาทั้งสัปดาห์\n\nคืนนั้นเธอลอยผ่านโต๊ะทำงาน แล้วเห็นกองจดหมายสูงท่วมหัว ใบแจ้งหนี้บัตรเครดิต ค่างวดรถ ค่าบ้าน ค่าน้ำค่าไฟ\n\nผีสาวอ่านไปทีละใบ แล้วค่อยๆ นั่งลงบนพื้น\n\nเช้าวันรุ่งขึ้น เจ้าของบ้านพบกระดาษโน้ตแปะตู้เย็นเขียนว่า 'สู้ๆ นะ เดี๋ยวคืนนี้ไม่หลอกแล้ว — ผี'",
      "§lตอนที่ 4: เครื่องรางนางกวัก§r\n\nป้าร้านส้มตำซื้อเครื่องรางนางกวักมาวางหน้าร้าน หวังให้ลูกค้าเข้าร้านเยอะๆ\n\nวันแรก ลูกค้ามาเต็มร้านจริงๆ ป้ายิ้มแก้มปริ\n\nวันที่สอง ลูกค้ายังเยอะอยู่ แต่ทุกคนสั่งแค่น้ำเปล่า\n\nวันที่สาม มีคนเดินเข้ามาถามทางไปร้านไก่ทอดยายน้อยสามสิบคน\n\nป้าหันไปมองนางกวักนิ่งๆ นางกวักก็กวักมือต่อไปอย่างขยันขันแข็ง ป้าเลยหันนางกวักให้กวักเข้าครกแทน",
      "§lตอนจบ: หมีตุ๊กตาของเด็กชายต้น§r\n\nเด็กชายต้นกลัวความมืดมาก ทุกคืนเขาจะกอดตุ๊กตาหมีแน่นจนมันหน้าบู้บี้\n\nคืนหนึ่งไฟดับทั้งหมู่บ้าน ต้นกอดหมีไว้ตัวสั่น แล้วก็ได้ยินเสียงเบาๆ จากในอ้อมแขน\n\n'ไม่ต้องกลัวนะ... แต่ช่วยคลายมือหน่อยได้ไหม หายใจไม่ออก'\n\nต้นร้องกรี๊ดดังจนไฟกลับมาติดเองทั้งหมู่บ้าน\n\nตั้งแต่วันนั้นไม่มีใครในหมู่บ้านกลัวความมืดอีกเลย พวกเขากลัวเสียงกรี๊ดของต้นแทน\n\n§8— จบเล่ม ขอบคุณที่อ่านจนจบ —"
    ]
  },
  "succubi:book_travel": {
    key: "book_travel",
    name: "นิตยสารเที่ยวทั่วไทย",
    sanity: 8,
    cooldown: 10,
    consumed: false,
    special: "",
    pages: [
      "§lฉบับพิเศษ: หนีความวุ่นวายสักวัน§r\n\nเมื่อไหร่ที่รู้สึกว่าโลกหมุนเร็วเกินไป ลองหยุดเดินสักครู่ หายใจลึกๆ แล้วนึกถึงที่ไหนสักแห่งที่ทำให้ใจสงบ\n\nนิตยสารฉบับนี้รวบรวมสี่ที่เที่ยวที่ทีมงานไปมาจริง ทั้งทะเล ภูเขา ตลาดน้ำ และหมู่บ้านเล็กๆ ที่ไม่มีใครรีบร้อน\n\nพลิกหน้าไปช้าๆ ไม่ต้องรีบ ที่เหล่านี้ไม่ได้หนีไปไหน",
      "§lทะเลอันดามันยามเช้า§r\n\nหกโมงเช้า น้ำทะเลยังเย็นและใสจนมองเห็นปลาตัวเล็กว่ายวนรอบข้อเท้า ทรายขาวละเอียดเหมือนแป้ง เรือหางยาวลำแรกเพิ่งออกจากฝั่ง\n\nชาวประมงยิ้มให้แล้วโบกมือทักทาย เสียงคลื่นซัดเบาๆ เป็นจังหวะ ช้ากว่าหัวใจคนเมืองครึ่งหนึ่ง\n\n§8เคล็ดลับ:§r ไปก่อนแดดแรง พกน้ำเปล่าหนึ่งขวด และทิ้งโทรศัพท์ไว้ในกระเป๋าสักชั่วโมง",
      "§lดอยสูงกับทะเลหมอก§r\n\nตีห้าครึ่ง อากาศหนาวจนเห็นลมหายใจเป็นควันขาว ทุกคนยืนเงียบรอพระอาทิตย์อยู่บนจุดชมวิว\n\nแล้วท้องฟ้าก็ค่อยๆ เปลี่ยนจากสีม่วงเป็นส้ม ทะเลหมอกด้านล่างลอยต่ำเหมือนปุยนุ่นผืนใหญ่ ยอดดอยโผล่ขึ้นมาเป็นเกาะเล็กๆ\n\nกาแฟร้อนแก้วเดียวในมือตอนนั้น อร่อยกว่ากาแฟทุกแก้วที่เคยกินมา\n\n§8เคล็ดลับ:§r เสื้อกันหนาวสำคัญกว่ากล้องถ่ายรูป",
      "§lตลาดน้ำยามเย็น§r\n\nเรือลำเล็กบรรทุกก๋วยเตี๋ยวเรือ ขนมครก และผลไม้ตามฤดูกาลลอยเรียงกันเต็มลำคลอง แม่ค้าส่งชามผ่านไม้ยาวขึ้นมาบนท่าได้แม่นยำไม่หกสักหยด\n\nพอฟ้าเริ่มมืด ตะเกียงตามบ้านริมน้ำก็ติดทีละดวง แสงไฟสะท้อนผิวน้ำเป็นทางยาว หิ่งห้อยตัวแรกบินออกมาจากต้นลำพู\n\nชามเล็กๆ ราคาไม่กี่บาท แต่ความอิ่มใจนั้นอยู่ได้ทั้งคืน",
      "§lหมู่บ้านที่ไม่มีใครรีบ§r\n\nลึกเข้าไปในหุบเขา มีหมู่บ้านเล็กๆ ที่ร้านค้าเปิดสายและปิดเร็ว ไม่มีใครถามว่าวันนี้ทำงานไปกี่ชั่วโมง\n\nคุณยายหน้าบ้านนั่งจักสานตะกร้าไปคุยไป เด็กๆ วิ่งไล่ลูกหมาไปตามถนนดิน ข้าวในนาเขียวจนแสบตา\n\nนักท่องเที่ยวคนหนึ่งเขียนไว้ในสมุดเยี่ยมว่า 'มาพักสองวัน แต่เหมือนได้พักใจมาทั้งปี'\n\n§8— จบฉบับ แล้วพบกันฉบับหน้า —"
    ]
  },
  "succubi:book_romance": {
    key: "book_romance",
    name: "นิยายรัก 'ใต้แสงจันทร์'",
    sanity: 15,
    cooldown: 20,
    consumed: false,
    special: "",
    pages: [
      "§lบทที่ 1: ร่มคันนั้น§r\n\nคืนนั้นดวงจันทร์เต็มดวง ท้องฟ้าไม่มีเมฆสักก้อน แต่เธอยังยื่นร่มสีฟ้าให้เขาอยู่ดี\n\n'ฝนไม่ได้ตกนะ' เขาพูดพลางหัวเราะ\n\n'รู้' เธอตอบ 'แต่เผื่อไว้ก่อน บางทีเรื่องดีๆ ก็มาเหมือนฝน ไม่ทันตั้งตัว'\n\nเขารับร่มไว้ทั้งที่ไม่เข้าใจ และไม่รู้เลยว่าร่มคันนั้นจะอยู่ข้างประตูห้องเขาไปอีกหลายปี",
      "§lบทที่ 2: ร้านน้ำชาตอนสามทุ่ม§r\n\nทั้งคู่เจอกันอีกครั้งที่ร้านน้ำชาเล็กๆ ท้ายตลาด เธอสั่งชาไทยหวานน้อย เขาสั่งมัทฉะแล้วบ่นว่าขม\n\nพวกเขาคุยกันเรื่องไร้สาระ ตั้งแต่ทำไมแมวชอบนั่งบนกล่อง จนถึงว่าถ้าโลกแตกพรุ่งนี้จะกินอะไรเป็นมื้อสุดท้าย\n\n'ข้าวไข่เจียว' เธอตอบทันที 'ง่ายที่สุด แต่อร่อยที่สุด เหมือนเรื่องบางเรื่องที่ไม่ต้องพยายามมาก'\n\nเขาจำประโยคนั้นได้ขึ้นใจ",
      "§lบทที่ 3: คืนที่ไฟดับ§r\n\nคืนหนึ่งไฟดับทั้งเมือง เธอโทรหาเขาด้วยเสียงสั่น เธอกลัวความมืดมาตั้งแต่เด็ก\n\nเขาไม่ได้ปลอบด้วยคำพูดยาวๆ แค่เปิดไฟฉายโทรศัพท์ แล้วเดินข้ามเมืองไปนั่งหน้าบ้านเธอ ส่องไฟไปที่หน้าต่างให้เธอเห็นว่ามีคนอยู่ตรงนั้น\n\n'ถ้าวันหนึ่งฉันหลงทาง เธอจะตามหาไหม'\n\n'ไม่ต้องตามหาหรอก ฉันจะเป็นแสงไฟ ให้เธอเดินกลับมาเอง'",
      "§lบทที่ 4: ระยะทาง§r\n\nงานใหม่ของเขาอยู่ไกลออกไปอีกฟากของประเทศ ทั้งคู่ไม่ได้ทะเลาะกัน ไม่ได้ร้องไห้ แค่เงียบไปนานกว่าปกติ\n\nทุกคืนเขาจะส่งรูปพระจันทร์มาให้เธอ บางคืนเต็มดวง บางคืนเป็นเสี้ยวบางๆ บางคืนมีแต่เมฆ\n\n'คืนนี้มองไม่เห็นเลย' เขาพิมพ์มา\n\n'ไม่เป็นไร' เธอตอบ 'รู้ว่ามันยังอยู่ตรงนั้นก็พอ'",
      "§lบทส่งท้าย: ใต้แสงจันทร์§r\n\nหลายปีต่อมา ทั้งคู่นั่งอยู่บนระเบียงบ้านหลังเล็ก ร่มสีฟ้าคันเดิมพิงอยู่ข้างประตู ขอบผ้าซีดไปตามเวลา\n\nพระจันทร์คืนนั้นเต็มดวงเหมือนคืนแรก เธอเอนหัวพิงไหล่เขา ไม่มีใครพูดอะไร และไม่มีใครต้องพูด\n\nรอบตัวมืดสนิท แต่ไม่มีใครกลัวความมืดอีกแล้ว\n\n§8— จบ —"
    ]
  },
  "succubi:book_mystery": {
    key: "book_mystery",
    name: "นิยายสืบสวน 'คดีบ้านร้าง'",
    sanity: 15,
    cooldown: 20,
    consumed: false,
    special: "",
    pages: [
      "§lบทที่ 1: รอยเท้าเปียก§r\n\nบ้านร้างท้ายซอยว่างมาสิบปี ไม่มีใครกล้าเดินผ่านหลังพระอาทิตย์ตก เช้าวันนั้นชาวบ้านแจ้งตำรวจว่าได้ยินเสียงเคาะจากข้างใน\n\nนักสืบหนุ่มผลักประตูเข้าไปคนเดียว พื้นไม้ส่งเสียงเอี๊ยดทุกก้าว และบนพื้นนั้นมีรอยเท้าเปียกเรียงเป็นแถว\n\nแปลกตรงที่ฝนไม่ได้ตกมาสามวันแล้ว\n\nเขาก้มลงดู รอยเท้าเล็กเท่าเท้าเด็ก และมันเดินตรงไปที่ประตูห้องใต้ดิน",
      "§lบทที่ 2: ผู้ต้องสงสัยสามคน§r\n\nนักสืบสอบปากคำคนแถวนั้น\n\n§lป้าร้านส้มตำ§r บอกว่าเห็นแสงไฟวูบวาบในบ้านทุกคืนวันศุกร์\n§lลุงคนขับสามล้อ§r สาบานว่าได้ยินเสียงเด็กร้องเพลงกล่อมเด็ก\n§lภารโรงโรงเรียน§r ตอบสั้นๆ ว่าไม่รู้เรื่อง แล้วรีบเดินหนี กางเกงของเขาเปียกถึงหัวเข่า\n\nนักสืบจดทุกอย่างลงสมุด แล้วขีดเส้นใต้คำว่า 'เปียก' สองครั้ง",
      "§lบทที่ 3: กุญแจที่ไขได้เกือบทุกประตู§r\n\nในลิ้นชักห้องครัว นักสืบพบพวงกุญแจเก่าสิบสองดอก เขาลองไขทุกประตูในบ้าน ห้องนอน ห้องน้ำ ตู้เสื้อผ้า ห้องเก็บของ ทุกดอกใช้ได้หมด\n\nยกเว้นประตูห้องใต้ดิน\n\nข้างประตูนั้นมีรอยขีดบนผนังเป็นขีดเล็กๆ นับวัน รวมแล้วสามร้อยหกสิบห้าขีดพอดี\n\nจากใต้ประตู มีน้ำเย็นเฉียบค่อยๆ ซึมออกมา",
      "§lบทที่ 4: ห้องใต้ดิน§r\n\nนักสืบยืมชะแลงจากร้านช่างมางัดประตู เสียงไม้แตกดังก้องไปทั้งซอย\n\nข้างล่างไม่มีศพ ไม่มีผี มีแต่ท่อน้ำประปาแตกที่รั่วมาเป็นปี กับกล่องไม้ใบหนึ่งที่เต็มไปด้วยของเล่นเด็ก รถไม้ ตุ๊กตาหมี และสมุดวาดรูปที่ลายเส้นตัวอักษรสั่นๆ\n\nหน้าสุดท้ายของสมุดเขียนว่า 'ถ้าพ่อกลับมา ช่วยบอกด้วยว่าหนูรอ'",
      "§lบทสุดท้าย: ความจริง§r\n\nภารโรงยอมพูดในที่สุด เขาคือพ่อของเด็กคนนั้น ลูกสาวย้ายไปอยู่กับแม่ตั้งแต่สิบปีก่อน ส่วนบ้านหลังนี้เขาขายไม่ลง\n\nทุกคืนวันศุกร์เขาแอบเข้ามาเปิดไฟ ร้องเพลงกล่อมเด็กเพลงเดิม และลุยน้ำจากท่อแตกไปนั่งข้างกล่องของเล่น รอยเท้าเล็กๆ ที่เห็นคือรองเท้าแตะเก่าของลูกสาวที่เขาใส่ไม่พอดีเท้า\n\nคดีปิด ไม่มีใครถูกจับ นักสืบช่วยซ่อมท่อประปา แล้วกลับบ้านไปกินข้าวไข่เจียวสูตรผู้บัญชาการ\n\n§8— จบ —"
    ]
  },
  "succubi:book_dharma": {
    key: "book_dharma",
    name: "หนังสือธรรมะ 'ใจสงบ'",
    sanity: 20,
    cooldown: 30,
    consumed: false,
    special: "calm",
    pages: [
      "§lบทนำ§r\n\nหนังสือเล่มนี้ไม่ได้สอนให้เลิกกลัว เพราะความกลัวเป็นเรื่องธรรมดาของทุกคน\n\nแต่อยากชวนให้รู้จักความกลัวให้ดีขึ้น ว่ามันมาจากไหน อยู่นานแค่ไหน และมันไปได้อย่างไร\n\nอ่านช้าๆ ทีละหน้า ไม่ต้องจำ ไม่ต้องเข้าใจทั้งหมดในครั้งเดียว ใจที่อ่านอย่างสบายๆ จะเก็บสิ่งที่ต้องการไว้เอง",
      "§lความกลัวเกิดจากใจ§r\n\nเสียงกิ่งไม้เคาะหน้าต่างเป็นเพียงเสียง แต่ใจเติมเรื่องราวให้มันเป็นมือที่พยายามเข้ามา\n\nเงาตรงมุมห้องเป็นเพียงเสื้อที่แขวนไว้ แต่ใจวาดให้มันมีดวงตา\n\nเมื่อรู้ทันว่าใจกำลังเล่าเรื่องให้ตัวเองฟัง ความกลัวก็เบาบางลงเอง เหมือนหมอกที่จางเมื่อแดดส่อง",
      "§lลมหายใจคือที่พัก§r\n\nเมื่อใจวุ่นวาย ให้กลับมาที่ลมหายใจ\n\nหายใจเข้า รู้ว่าหายใจเข้า\nหายใจออก รู้ว่าหายใจออก\n\nไม่ต้องบังคับให้ยาวหรือสั้น แค่เฝ้าดูมันเหมือนดูคลื่นกระทบฝั่ง ลองนับหนึ่งถึงสิบ ถ้าหลงก็เริ่มนับใหม่ ไม่มีใครตัดคะแนน\n\nลมหายใจอยู่กับเราเสมอ แม้ในคืนที่มืดที่สุด",
      "§lสิ่งที่ผ่านมาและผ่านไป§r\n\nความสุขมาแล้วก็ไป ความทุกข์มาแล้วก็ไป เสียงเคาะประตูกลางดึกก็เช่นกัน มันดังขึ้นแล้วก็เงียบลง\n\nไม่มีสิ่งใดอยู่กับเราตลอดไป เว้นแต่เราจะยึดมันไว้เอง\n\nลองปล่อยมือจากเรื่องที่ทำให้ใจหนักสักเรื่อง แม้เพียงคืนนี้คืนเดียว แล้วสังเกตว่าใจเบาขึ้นแค่ไหน",
      "§lบทส่งท้าย§r\n\nสิ่งที่มองไม่เห็นไม่อาจทำร้ายใจที่สงบได้\n\nเมื่อปิดหนังสือเล่มนี้ ขอให้ใจของผู้อ่านมั่นคงเหมือนภูเขา แม้ลมพัดแรงเพียงใดก็ไม่หวั่นไหว\n\nขอให้นอนหลับสบาย ตื่นมาพร้อมใจที่แจ่มใส และมีเมตตาต่อตัวเองเท่ากับที่มีต่อผู้อื่น\n\n§8— ขออนุโมทนา —"
    ]
  },
  "succubi:book_prayer": {
    key: "book_prayer",
    name: "หนังสือสวดมนต์",
    sanity: 6,
    cooldown: 10,
    consumed: false,
    special: "ward",
    pages: [
      "§lบทบูชาพระรัตนตรัย§r\n\nอะระหัง สัมมาสัมพุทโธ ภะคะวา\nพุทธัง ภะคะวันตัง อะภิวาเทมิ\n\nสวากขาโต ภะคะวะตา ธัมโม\nธัมมัง นะมัสสามิ\n\nสุปะฏิปันโน ภะคะวะโต สาวะกะสังโฆ\nสังฆัง นะมามิ\n\n§8(กราบ ๓ ครั้ง แล้วตั้งใจสวดบทต่อไป)",
      "§lบทสรรเสริญพระพุทธคุณ§r\n\nอิติปิ โส ภะคะวา อะระหัง สัมมาสัมพุทโธ\nวิชชาจะระณะสัมปันโน สุคะโต โลกะวิทู\nอะนุตตะโร ปุริสะธัมมะสาระถิ\nสัตถา เทวะมะนุสสานัง พุทโธ ภะคะวาติ",
      "§lบทสรรเสริญพระธรรมคุณ§r\n\nสวากขาโต ภะคะวะตา ธัมโม\nสันทิฏฐิโก อะกาลิโก เอหิปัสสิโก\nโอปะนะยิโก ปัจจัตตัง เวทิตัพโพ วิญญูหีติ\n\n§lบทสรรเสริญพระสังฆคุณ§r\n\nสุปะฏิปันโน ภะคะวะโต สาวะกะสังโฆ\nอุชุปะฏิปันโน ภะคะวะโต สาวะกะสังโฆ ...",
      "§lบทแผ่เมตตา§r\n\nสัพเพ สัตตา\nสัตว์ทั้งหลายที่เป็นเพื่อนทุกข์ เกิด แก่ เจ็บ ตาย ด้วยกันทั้งหมดทั้งสิ้น\n\nอะเวรา โหนตุ จงเป็นสุขเป็นสุขเถิด อย่าได้มีเวรแก่กันและกันเลย\nอัพยาปัชฌา โหนตุ อย่าได้พยาบาทเบียดเบียนซึ่งกันและกันเลย\nอะนีฆา โหนตุ อย่าได้มีความทุกข์กายทุกข์ใจเลย\nสุขี อัตตานัง ปะริหะรันตุ จงมีความสุขกายสุขใจ รักษาตนให้พ้นจากทุกข์ภัยทั้งสิ้นเถิด",
      "§lคำอธิษฐาน§r\n\nด้วยอานุภาพแห่งคุณพระศรีรัตนตรัย ขอให้ข้าพเจ้าแคล้วคลาดจากสิ่งไม่ดีทั้งปวง ทั้งที่มองเห็นและมองไม่เห็น\n\nขอให้เสียงแปลกๆ ในความมืดผ่านเลยไป ขอให้เงาที่ยืนมองกลับไปสู่ที่ของมัน\n\nขอให้เพื่อนร่วมทางทุกคนปลอดภัย กลับถึงบ้านโดยสวัสดิภาพ\n\n§8— สาธุ สาธุ สาธุ —"
    ]
  },
  "succubi:book_coloring": {
    key: "book_coloring",
    name: "สมุดระบายสี + สีเทียน",
    sanity: 8,
    cooldown: 10,
    consumed: false,
    special: "",
    pages: [
      "§lหน้า 1: แมวนอนกลางวัน§r\n\nรูปแมวอ้วนตัวหนึ่งขดตัวหลับอยู่บนหมอนนุ่ม หางพาดลงมาจากขอบเก้าอี้\n\nคุณเลือกสีเทียนสีส้ม แล้วค่อยๆ ระบายลงบนตัวแมว เส้นสีออกนอกขอบไปนิดหน่อยตรงหู แต่ไม่เป็นไรเลย\n\nหมอนใบนั้นคุณระบายสีฟ้าอ่อน ส่วนหนวดแมวปล่อยไว้สีขาวเหมือนเดิม\n\nแมวในรูปดูหลับสบายกว่าเดิม เหมือนมันรู้ว่ามีคนมาแต่งตัวให้",
      "§lหน้า 2: บึงดอกบัว§r\n\nดอกบัวสามดอกลอยอยู่กลางบึง ใบบัวกลมใหญ่ มีกบตัวเล็กนั่งอยู่บนใบหนึ่ง\n\nคุณใช้สีชมพูอ่อนไล่จากปลายกลีบเข้ามาหาเกสร แล้วเติมสีเหลืองตรงกลาง ใบบัวสีเขียวเข้ม ส่วนน้ำในบึงคุณผสมฟ้ากับเขียวจนได้สีที่ชอบ\n\nกบตัวนั้น คุณตัดสินใจระบายเป็นสีม่วง ก็แค่อยากให้มันพิเศษกว่ากบทั่วไป",
      "§lหน้า 3: บ้านไฟเปิด§r\n\nบ้านไม้หลังเล็กตั้งอยู่ใต้ต้นไม้ใหญ่ ท้องฟ้าด้านหลังเป็นกลางคืน มีดาวสามดวง\n\nคุณระบายหน้าต่างทุกบานเป็นสีเหลืองสว่าง เหมือนมีไฟเปิดอยู่ข้างใน หลังคาสีแดงอิฐ ต้นไม้สีเขียวเข้ม ท้องฟ้าสีน้ำเงินกดแรงๆ จนมือเมื่อย\n\nพอระบายเสร็จ บ้านหลังนั้นดูอบอุ่นอย่างบอกไม่ถูก เหมือนมีใครรอคุณกลับบ้านอยู่",
      "§lหน้า 4: หน้าว่างสำหรับคุณ§r\n\nหน้าสุดท้ายไม่มีลายเส้นอะไรเลย มีแค่คำเขียนเล็กๆ มุมกระดาษว่า 'วาดอะไรก็ได้ที่ทำให้ยิ้ม'\n\nคุณนั่งคิดอยู่นาน แล้ววาดวงกลมสีเหลืองใหญ่ๆ เติมตาสองจุดกับปากยิ้มกว้าง\n\nไม่ใช่รูปที่สวยที่สุดในโลก แต่เป็นรูปที่คุณชอบที่สุดในเล่มนี้\n\n§8— สีเทียนเหลือครึ่งกล่อง ไว้ระบายต่อวันหลัง —"
    ]
  },
  "succubi:book_survival": {
    key: "book_survival",
    name: "คู่มือเอาชีวิตรอดฉบับพกพา",
    sanity: 5,
    cooldown: 5,
    consumed: false,
    special: "guide",
    pages: [
      "§lวงสี่วงเหนือช่องของ§r\n\n§cหัวใจ§r = เลือด ยิ่งตัวสูงเลือดยิ่งเยอะ\n§6น่องไก่§r = ความหิว\n§bหยดน้ำ§r = ความกระหาย\n§dสมอง§r = สติ\n\nลูกศรเล็กๆ เหนือวง บอกว่าค่านั้นกำลังเพิ่ม (ชี้ขึ้น) หรือลด (ชี้ลง) ยิ่งหลายอันยิ่งเร็ว\n\nนาฬิกามุมขวาบนบอกช่วงเวลา สีเหลือง = กลางวัน สีแดง = พลบค่ำ สีน้ำเงิน = กลางคืน ตรงกลางคือวันที่เท่าไหร่ที่คุณรอดมาได้",
      "§lน้ำและอาหาร§r\n\nน้ำลดตลอดเวลา วิ่งแล้วลดเร็วขึ้น อยู่เนเธอร์ยิ่งคอแห้ง ต่ำกว่า 30% เดินช้า หมดเมื่อไหร่เลือดจะค่อยๆ ลด\n\nดื่มน้ำ นม ซุป หรือกินผลไม้ช่วยได้ ของเผ็ดของเค็มทำให้คอแห้งกว่าเดิม ร้านยามีเกลือแร่ ORS\n\nอาหารสุกดีกว่าของดิบเสมอ เนื้อดิบทำให้สติลด อาหารอร่อยจากร้านค้าช่วยทั้งท้องและใจ",
      "§lสติ และสิ่งที่มากับความมืด§r\n\nสติลดเมื่อ: โดนตี อยู่ใกล้มอนสเตอร์ อยู่เนเธอร์หรือดิเอนด์ อยู่กลางแจ้งตอนกลางคืน อยู่ในที่มืดโดยไม่มีไฟ และเจอเรื่องแปลกๆ\n\nสติเพิ่มเมื่อ: กินของอร่อย นอนหลับ อยู่ใกล้เพื่อน นั่งข้างกองไฟ เก็บดอกไม้ กอดตุ๊กตา อ่านหนังสือ\n\nสติยิ่งต่ำ จอยิ่งซ่าเหมือนทีวีเสีย ต่ำกว่า 15% เงาจะมาหาคุณคนเดียว คนอื่นมองไม่เห็นมัน ตีมันจนสลายได้ หรือรีบทำให้สติกลับมา",
      "§lส่วนสูงและร่างกาย§r\n\nเปิดกระเป๋าตังค์ > ตั้งค่า > ปรับส่วนสูง\n\nตัวเตี้ย: เลือดน้อย วิ่งไว ตีเบา ตกจากที่สูงเจ็บน้อย หิวช้า\nตัวสูง: เลือดเยอะ เดินช้า ตีแรง ตกแรงกว่า หิวไว\n\nเปลี่ยนได้เป็นระยะ และเปลี่ยนไม่ได้ช่วงเพิ่งต่อสู้ ถ้ากดรีเซ็ตจะกลับเป็นส่วนสูงมาตรฐาน",
      "§lเงิน ร้านค้า และการรักษา§r\n\nกระเป๋าตังค์อยู่ช่องสุดท้ายเสมอ ฝาก ถอน และดูยอดเงินได้ในนั้น\n\nร้านค้าและตู้กดน้ำ: กด 'ใส่เงินหมด' แล้วเลือกของ เงินที่เหลือทอนคืนตอนปิดหน้าต่าง\n\nผ้าพันแผล ชุดปฐมพยาบาล และเข็มฉีดยา ใช้กับตัวเองหรือเพื่อนได้ ยิ่งเลือดน้อยยิ่งต้องรีบ\n\nเครื่องราง: กระเป๋าตังค์ > เครื่องราง ใส่ได้ 4 ชิ้น แต่ละชิ้นมีทั้งข้อดีและข้อเสีย",
      "§lกฎเหล็กของผู้รอดชีวิต§r\n\n1. ถ้าเห็นป้ายประกาศกฎ ทำตามกฎนั้นเสมอ แม้จะดูไร้สาระ\n2. ถ้าได้ยินเสียงเคาะสามครั้ง อย่าเปิดประตู\n3. รูปปั้นที่ขยับได้ ขยับเฉพาะตอนไม่มีใครมอง\n4. เดินเป็นกลุ่มตอนกลางคืน และพกไฟไว้ในมือ\n5. นอนให้พอ ความฝันดีๆ คือยาที่ถูกที่สุด\n\n§8— ขอให้รอดไปอีกหลายวัน —"
    ]
  },
  "succubi:book_ghost": {
    key: "book_ghost",
    name: "หนังสือเล่มดำ 'เรื่องเล่าต้องห้าม'",
    sanity: -10,
    cooldown: 15,
    consumed: false,
    special: "cursed",
    pages: [
      "§4คำเตือน§r\n\nหนังสือเล่มนี้ไม่มีชื่อผู้เขียน ไม่มีสำนักพิมพ์ ไม่มีวันที่ ปกหนังแข็งเย็นเฉียบแม้วางไว้กลางแดด\n\nหน้าแรกเขียนด้วยหมึกสีแดงคล้ำว่า\n\n'ถ้าคุณอ่านถึงบรรทัดนี้ แปลว่ามันรู้แล้วว่าคุณอยู่ที่ไหน'\n\nลายมือสั่นเทา ตัวอักษรบางตัวเขียนซ้ำจนกระดาษขาด",
      "§lเรื่องที่หนึ่ง: เสียงเคาะ§r\n\n'ถ้าได้ยินเสียงเคาะประตูสามครั้งหลังเที่ยงคืน อย่าเปิด อย่าถามว่าใคร อย่าส่องตาแมว'\n\nคนเขียนเล่าว่าเพื่อนบ้านของเขาเปิดประตูในคืนหนึ่ง ไม่มีใครอยู่หน้าบ้าน มีแค่รอยเท้าเปียกเดินเข้ามาในบ้าน และไม่มีรอยเดินออกไป\n\nเช้าวันต่อมา เพื่อนบ้านคนนั้นยังอยู่ แต่เขาไม่เคยหันหลังให้ประตูอีกเลย",
      "§lเรื่องที่สอง: รูปปั้น§r\n\n'ถ้าเห็นรูปปั้นอยู่ใกล้กว่าเมื่อวาน อย่ากะพริบตา อย่าหันหลัง ค่อยๆ เดินถอยออกมาจนพ้นสายตามัน'\n\nมีคนเคยวัดระยะไว้ด้วยเชือก เช้าวันแรกห่างสิบก้าว เช้าวันที่สองเหลือเจ็ด เช้าวันที่สามเหลือสาม\n\nหน้านี้มีรอยขีดเล็บยาวๆ ลากลงไปถึงขอบกระดาษ แล้วบันทึกของคนนั้นก็จบลงแค่นั้น",
      "§lเรื่องที่สาม: เงาที่ไม่ใช่ของใคร§r\n\n'เมื่อใจของคุณแตกร้าว เงาจะเริ่มมีรูปร่าง คนอื่นจะมองไม่เห็นมัน และจะคิดว่าคุณบ้า'\n\n'มันมีแขนยาวเกินไป ตาแดงเหมือนถ่านที่ยังไม่มอด มันไม่รีบ เพราะมันรู้ว่าคุณหนีไปไหนไม่ได้'\n\n'วิธีเดียวคือทำให้ใจกลับมามั่นคง หรือสู้กับมันด้วยมือตัวเอง'",
      "§4หน้าสุดท้าย§r\n\nหน้านี้ว่างเปล่า\n\n...ไม่สิ ตอนเปิดครั้งแรกมันว่างเปล่า\n\nตอนนี้มีตัวอักษรค่อยๆ ซึมขึ้นมาจากเนื้อกระดาษ เหมือนมีคนเขียนจากอีกด้าน\n\n'ขอบคุณที่อ่านจนจบ'\n'ตอนนี้ถึงตาเราอ่านคุณบ้าง'\n\nกระดาษชื้นเหมือนเพิ่งมีมือเย็นๆ แตะผ่าน"
    ]
  }
};

// Newspaper: a front-page story, two inside pages, and the back page, drawn fresh every issue
const NEWS = [
  { h: "พบเงาดำยืนมองชาวบ้านกลางทุ่ง", b: "ชาวบ้านหลายรายยืนยันตรงกันว่าเห็นร่างสูงผิดปกติยืนนิ่งกลางทุ่งหญ้าช่วงพลบค่ำ พอเดินเข้าไปใกล้ร่างนั้นก็หายไป ตำรวจยังไม่พบเบาะแส แต่ขอให้ประชาชนเดินทางเป็นกลุ่มหลังมืด" },
  { h: "ไก่ทอดยายน้อยหมดเกลี้ยงตั้งแต่เช้า", b: "ลูกค้าต่อคิวยาวจากหน้าร้านไก่ทอดไปจนถึงแผงขายยา ยายน้อยเผยว่าวันนี้ทอดไปกว่าสามร้อยชิ้น 'สูตรไม่มีอะไรพิเศษ แค่ทอดด้วยใจ' ยายกล่าวพร้อมรอยยิ้ม" },
  { h: "{who} อ้างเห็นรูปปั้นขยับเอง", b: "{who} เล่าว่ารูปปั้นหินหน้าอาคารร้างอยู่ใกล้ขึ้นทุกครั้งที่หันกลับไปมอง ผู้สื่อข่าวลงพื้นที่แต่ไม่พบความผิดปกติ ขณะเขียนข่าวนี้ รูปปั้นดูเหมือนจะหันหน้ามาทางโต๊ะบรรณาธิการ" },
  { h: "หมอเตือน สติต่ำอันตรายกว่าที่คิด", b: "แพทย์ประจำชุมชนแนะนำให้อ่านหนังสือ กินของอร่อย นอนให้พอ และอยู่ใกล้เพื่อน ผู้ที่เริ่มเห็นภาพซ่าเหมือนทีวีเสียควรพักผ่อนทันที และอย่าอยู่ในที่มืดคนเดียว" },
  { h: "ร้านน้ำชาฮารุโตะปฏิเสธข่าวลือ", b: "ท่านฮารุโตะยืนยันว่าเพลงในร้านไม่ได้เปิดเองตอนตีสาม 'เครื่องเล่นเพลงถอดปลั๊กไว้ทุกคืน' ท่านกล่าว ก่อนจะหยุดพูดไปครู่หนึ่งแล้วเปลี่ยนเรื่องไปแนะนำชาไทยสูตรใหม่" },
  { h: "{who} คว้ารางวัลนักอ่านประจำเดือน", b: "ห้องสมุดชุมชนรายงานว่า {who} ยืมหนังสือไปมากที่สุดในเดือนนี้ รวมถึงหนังสือเล่มดำที่ไม่มีใครกล้ายืม เจ้าหน้าที่ขอให้คืนเล่มนั้นโดยเร็ว เพราะชั้นหนังสือว่างตรงนั้นเริ่มมีกลิ่นแปลกๆ" },
  { h: "ป้ายกฎประหลาดโผล่หน้าอาคารร้าง", b: "ป้ายไม้เขียนด้วยลายมือว่า 'ห้ามวิ่ง ห้ามหันหลัง ห้ามตอบเมื่อมีคนเรียกชื่อ' ถูกพบหน้าอาคารร้างย่านเก่า ผู้ที่ฝ่าฝืนเล่าว่ารู้สึกเหมือนถูกจ้องมองตลอดทางกลับบ้าน" },
  { h: "ข้าวกะเพราไข่ดาวยังคุ้มที่สุดในย่าน", b: "ผลสำรวจราคาอาหารประจำสัปดาห์พบว่าข้าวกะเพราไข่ดาวในร้านสะดวกซื้อยังคงคุ้มค่าที่สุด ตามมาด้วยข้าวไข่เจียวสูตรผู้บัญชาการ ส่วนราคาเกลือแร่ ORS ที่ร้านยายังคงที่" },
  { h: "ค้างคาวแตกฝูงกลางเมือง", b: "มีผู้พบเห็นค้างคาวจำนวนมากบินออกมาจากความมืดทั้งที่บริเวณนั้นไม่มีถ้ำ นักวิชาการชี้ว่าอาจเกิดจากเสียงบางอย่างที่คนไม่ได้ยิน และแนะนำให้ปิดหน้าต่างก่อนนอน" },
  { h: "เสียงเคาะประตูปริศนายังไม่หยุด", b: "ผลสำรวจพบว่าชาวเซิร์ฟ 9 ใน 10 คนเคยได้ยินเสียงเคาะสามครั้งทั้งที่ไม่มีใครอยู่หน้าบ้าน ช่างซ่อมบ้านยืนยันว่าประตูทุกบานปกติดี 'ปัญหาไม่ได้อยู่ที่ประตู' เขากล่าว" },
  { h: "{who} ซื้อเครื่องรางไปครบชุด", b: "แผงพระเครื่องรายงานว่า {who} เหมาเครื่องรางไปหลายชิ้นในวันเดียว คนขายเตือนว่าเครื่องรางทุกชิ้นมีทั้งคุณและโทษ ควรเลือกใส่ให้เข้ากับการเดินทาง" },
  { h: "กองไฟกลางลานกลายเป็นจุดนัดพบ", b: "หลังข่าวเงาดำแพร่สะพัด ชาวบ้านเริ่มก่อกองไฟรวมตัวกันยามค่ำ หลายคนบอกว่าแค่นั่งข้างไฟก็รู้สึกใจชื้นขึ้น บางคนเก็บดอกไม้มาวางรอบกองไฟเพื่อความสบายใจ" }
];
const WEATHER = ["แดดจัดตลอดวัน ดื่มน้ำบ่อยๆ", "ฝนตกเป็นช่วงๆ ระวังพื้นลื่น", "หมอกลงหนาช่วงเช้า ทัศนวิสัยต่ำ", "ท้องฟ้าโปร่ง คืนนี้พระจันทร์สวย", "ลมแรง เมฆดำตั้งเค้าช่วงค่ำ"];
const HOROSCOPE = ["วันนี้มีโชคเรื่องอาหาร ร้านที่เดินผ่านอาจมีของอร่อย", "ระวังเสียงเรียกจากทางด้านหลัง อย่าเพิ่งหันไปตอบ", "เพื่อนเก่าจะนำข่าวดีมาให้", "เหมาะกับการนอนหลับให้เต็มอิ่ม", "สีมงคลคือสีแดงของกองไฟ", "อย่ากะพริบตานานเกินไปเวลาอยู่ใกล้รูปปั้น"];
const ADS = ["รับซ่อมประตูที่เปิดเอง ราคากันเอง ติดต่อช่างหน้าตลาด", "ตุ๊กตาหมีกอดคลายเครียด มีขายที่ร้านสะดวกซื้อ", "ร้านส้มตำครกทอง ลดราคาทุกวันศุกร์ (ยกเว้นคืนวันศุกร์)", "หาเพื่อนร่วมเดินทางกลางคืน มีไฟฉายเป็นของตัวเอง"];

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

export function newsPages(seedNames) {
  const names = seedNames ?? world.getAllPlayers().map((p) => p.name);
  const who = () => (names.length ? names[Math.floor(Math.random() * names.length)] : "ชาวบ้าน");
  const pool = [...NEWS].sort(() => Math.random() - 0.5);
  const fill = (s, name) => s.replace(/\{who\}/g, name);
  const story = (n, big) => {
    const name = who();
    return `${big ? "§l§4" : "§l"}${fill(n.h, name)}§r\n${fill(n.b, name)}`;
  };
  const pick = (list) => list[Math.floor(Math.random() * list.length)];
  const ads = [...ADS].sort(() => Math.random() - 0.5);
  const day = (() => {
    try {
      return world.getDay() + 1;
    } catch (e) {
      return 1;
    }
  })();
  return [
    `§8ฉบับวันที่ ${day} · ข่าวหน้าหนึ่ง§r\n\n${story(pool[0], true)}`,
    `${story(pool[1])}\n\n${story(pool[2])}`,
    `${story(pool[3])}\n\n${story(pool[4])}`,
    `§lพยากรณ์อากาศ§r\n${pick(WEATHER)}\n\n§lดวงประจำวัน§r\n${pick(HOROSCOPE)}\n\n§lประกาศย่อย§r\n${ads.slice(0, 2).map((a) => `· ${a}`).join("\n")}`
  ];
}

// The book window holds about 13 lines of 70 letters (plus the page number). A page that would run under the
// buttons is split at a paragraph break (or a line break) and carries on on the next page.
const LINE_CHARS = 70;
const PAGE_LINES = 12;
const linesOf = (text) =>
  text.replace(/§./g, "").split("\n").reduce((n, line) => n + Math.max(1, Math.ceil(line.length / LINE_CHARS)), 0);

export function fitPages(pages) {
  const out = [];
  for (const page of pages) {
    let rest = String(page);
    while (linesOf(rest) > PAGE_LINES) {
      const parts = rest.split("\n");
      let take = parts.length - 1;
      while (take > 1 && linesOf(parts.slice(0, take).join("\n")) > PAGE_LINES) take--;
      out.push(parts.slice(0, take).join("\n").trimEnd());
      rest = parts.slice(take).join("\n").replace(/^\n+/, "");
    }
    if (rest.trim()) out.push(rest);
  }
  return out;
}

// One page of a book in the book window; « ก่อนหน้า is greyed on the first page
function bookForm(title, key, theme, text, page, count) {
  const last = page >= count - 1;
  return new ActionFormData()
    .title(`§l${title}${BOOK_FLAG}${theme ? THEME[theme] : ""}${iconFlag(key)}`)
    .body(`${text}\n\n§r§8— หน้า ${page + 1} / ${count} —`)
    .button(page > 0 ? "§0ก่อนหน้า" : "§7ก่อนหน้า", `${BTN}btn_prev${page > 0 ? "" : "_off"}`)
    .button(last ? "§2อ่านจบ" : "§0ถัดไป", `${BTN}${last ? "btn_done" : "btn_next"}`)
    .button("§4ปิด", `${BTN}btn_close`);
}

const bookTheme = (book) => (book.special === "cursed" ? "cursed" : book.special === "news" ? "news" : "");

export async function readBook(player, id, page = 0, pages = undefined) {
  const book = BOOKS[id];
  if (!book) return;
  if (!pages) pages = fitPages(book.special === "news" ? newsPages() : book.pages);
  const r = await show(bookForm(book.name, book.key, bookTheme(book), pages[page], page, pages.length), player);
  if (!r || r.canceled || r.selection === 2) return;
  if (r.selection === 0) return readBook(player, id, Math.max(0, page - 1), pages);
  if (page < pages.length - 1) {
    try {
      player.playSound("item.book.page_turn", { volume: 0.6 });
    } catch (e) {}
    return readBook(player, id, page + 1, pages);
  }
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
  sheets = sheets ?? fitPages(bookSheets(book.pages));
  const text = `${page === 0 && book.author ? `§8โดย ${book.author}\n\n` : ""}§0${sheets[page]}`;
  const r = await show(bookForm(book.title, "book_custom", "", text, page, sheets.length), player);
  if (!r || r.canceled || r.selection === 2) return;
  if (r.selection === 0) return readCustom(player, book, id, Math.max(0, page - 1), sheets);
  if (page < sheets.length - 1) return readCustom(player, book, id, page + 1, sheets);
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
