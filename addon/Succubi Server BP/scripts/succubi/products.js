import { SANITY_BY_ID } from "./sanity_values.js";
// GENERATED from build/prod_data.py - drinks & snacks sold by the vending machines
export const DRINKS = [
  {
    "key": "water_bottle",
    "id": "succubi:drink_water_bottle",
    "name": "น้ำดื่ม",
    "price": 7,
    "thirst": 5.0,
    "effects": [],
    "lore": [
      "§7น้ำเปล่าใสสะอาด ไม่มีอะไรแอบแฝง",
      "§bดับกระหาย §f+5"
    ]
  },
  {
    "key": "pepsi",
    "id": "succubi:drink_pepsi",
    "name": "เป๊ปซี่",
    "price": 16,
    "thirst": 8.0,
    "effects": [
      {
        "effect": "haste",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ซ่าปลุกมือให้ขยับไวขึ้น",
      "§bดับกระหาย §f+8"
    ]
  },
  {
    "key": "fanta_orange",
    "id": "succubi:drink_fanta_orange",
    "name": "แฟนต้า น้ำส้ม",
    "price": 16,
    "thirst": 8.0,
    "effects": [
      {
        "effect": "jump_boost",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ส้มซ่าเด้งดึ๋ง ตัวเบาหวิว",
      "§bดับกระหาย §f+8"
    ]
  },
  {
    "key": "sprite",
    "id": "succubi:drink_sprite",
    "name": "สไปรท์",
    "price": 16,
    "thirst": 8.0,
    "effects": [
      {
        "effect": "water_breathing",
        "seconds": 40,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ใสเย็นดุจธารน้ำ หายใจโล่งปอด",
      "§bดับกระหาย §f+8"
    ]
  },
  {
    "key": "coca_cola",
    "id": "succubi:drink_coca_cola",
    "name": "โคคา-โคล่า",
    "price": 17,
    "thirst": 8.0,
    "effects": [
      {
        "effect": "speed",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ซ่าจนขาอยากออกวิ่ง",
      "§bดับกระหาย §f+8"
    ]
  },
  {
    "key": "schweppes",
    "id": "succubi:drink_schweppes",
    "name": "ชเวปส์",
    "price": 17,
    "thirst": 8.0,
    "effects": [
      {
        "effect": "fire_resistance",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7เย็นซ่า สู้ความร้อนได้ทุกรูปแบบ",
      "§bดับกระหาย §f+8"
    ]
  },
  {
    "key": "boss_coffee",
    "id": "succubi:drink_boss_coffee",
    "name": "บอส คอฟฟี่",
    "price": 20,
    "thirst": 9.0,
    "effects": [
      {
        "effect": "night_vision",
        "seconds": 60,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7กาแฟเข้ม ตาสว่างแม้ในความมืด",
      "§bดับกระหาย §f+9"
    ]
  },
  {
    "key": "pocari_sweat",
    "id": "succubi:drink_pocari_sweat",
    "name": "โพคารี่ สเวท",
    "price": 22,
    "thirst": 9.5,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 10,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7เกลือแร่ช่วยให้ร่างกายค่อยๆ ฟื้นตัว",
      "§bดับกระหาย §f+9.5"
    ]
  },
  {
    "key": "redbull",
    "id": "succubi:drink_redbull",
    "name": "เรดบูล",
    "price": 25,
    "thirst": 10.5,
    "effects": [
      {
        "effect": "slow_falling",
        "seconds": 30,
        "amplifier": 0
      },
      {
        "effect": "strength",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ตัวเบาเหมือนจะบินได้ แรงเต็มแขน",
      "§bดับกระหาย §f+10.5"
    ]
  },
  {
    "key": "green_tea",
    "id": "succubi:drink_green_tea",
    "name": "ชาเขียวญี่ปุ่น",
    "price": 35,
    "thirst": 13.5,
    "effects": [
      {
        "effect": "absorption",
        "seconds": 60,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ชาเขียวแท้ ร่างกายรู้สึกแกร่งขึ้น",
      "§bดับกระหาย §f+13.5"
    ]
  },
  {
    "key": "monster_energy",
    "id": "succubi:drink_monster_energy",
    "name": "มอนสเตอร์ เอนเนอร์จี",
    "price": 45,
    "thirst": 16.0,
    "effects": [
      {
        "effect": "strength",
        "seconds": 45,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 45,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7พลังล้นทะลัก ทั้งแรงทั้งไว",
      "§bดับกระหาย §f+16"
    ]
  }
];

export const SNACKS = [
  {
    "key": "wafer",
    "id": "succubi:snack_wafer",
    "name": "เวเฟอร์ช็อกโกแลต",
    "price": 12,
    "food": 3,
    "saturation": 0.4,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7กรอบเป็นชั้นๆ หวานกำลังดี",
      "§6อิ่มท้อง §f+3"
    ]
  },
  {
    "key": "jelly",
    "id": "succubi:snack_jelly",
    "name": "เยลลี่ผลไม้",
    "price": 12,
    "food": 3,
    "saturation": 0.3,
    "thirst": 1,
    "effects": [],
    "lore": [
      "§7หนึบหนับ ชุ่มคอเล็กน้อย",
      "§6อิ่มท้อง §f+3",
      "§bดับกระหาย §f+1"
    ]
  },
  {
    "key": "prawn_crackers",
    "id": "succubi:snack_prawn_crackers",
    "name": "ข้าวเกรียบกุ้ง",
    "price": 15,
    "food": 4,
    "saturation": 0.3,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7กรอบฟู หอมกุ้งทุกคำ",
      "§6อิ่มท้อง §f+4"
    ]
  },
  {
    "key": "cream_bun",
    "id": "succubi:snack_cream_bun",
    "name": "ขนมปังไส้ครีม",
    "price": 15,
    "food": 4,
    "saturation": 0.8,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7นุ่มฟู อิ่มท้องนาน",
      "§6อิ่มท้อง §f+4"
    ]
  },
  {
    "key": "chips",
    "id": "succubi:snack_chips",
    "name": "มันฝรั่งทอดกรอบ",
    "price": 20,
    "food": 4,
    "saturation": 0.3,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7กรอบเค็ม กินเพลินจนหมดถุง",
      "§6อิ่มท้อง §f+4"
    ]
  },
  {
    "key": "fish_strips",
    "id": "succubi:snack_fish_strips",
    "name": "ปลาเส้นปรุงรส",
    "price": 20,
    "food": 4,
    "saturation": 0.5,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7เคี้ยวหนึบ รสเข้มข้น",
      "§6อิ่มท้อง §f+4"
    ]
  },
  {
    "key": "cookies",
    "id": "succubi:snack_cookies",
    "name": "คุกกี้ช็อกโกแลตชิพ",
    "price": 25,
    "food": 5,
    "saturation": 0.5,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7หอมเนย ช็อกชิพเต็มคำ",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "biscuit_sticks",
    "id": "succubi:snack_biscuit_sticks",
    "name": "บิสกิตแท่งเคลือบช็อกโกแลต",
    "price": 25,
    "food": 5,
    "saturation": 0.4,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7แท่งกรอบเคลือบช็อกโกแลต",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "seaweed",
    "id": "succubi:snack_seaweed",
    "name": "สาหร่ายทอดกรอบ",
    "price": 30,
    "food": 6,
    "saturation": 0.4,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7บางกรอบ หอมกลิ่นทะเล",
      "§6อิ่มท้อง §f+6"
    ]
  },
  {
    "key": "chocolate",
    "id": "succubi:snack_chocolate",
    "name": "ช็อกโกแลตแท่ง",
    "price": 30,
    "food": 6,
    "saturation": 0.6,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7เข้มข้น ละลายในปาก",
      "§6อิ่มท้อง §f+6"
    ]
  },
  {
    "key": "chips_tube",
    "id": "succubi:snack_chips_tube",
    "name": "มันฝรั่งแผ่นกระป๋อง",
    "price": 42,
    "food": 7,
    "saturation": 0.4,
    "thirst": 0,
    "effects": [],
    "lore": [
      "§7แผ่นเรียงสวย กรอบเท่ากันทุกแผ่น",
      "§6อิ่มท้อง §f+7"
    ]
  }
];

// GENERATED - dishes sold by the kiosk shops (models from the Food Items pack)
export const KIOSK_FOODS = [
  {
    "key": "somtum_plate",
    "id": "food:somtum_plate",
    "name": "ส้มตำไทย ครกทอง",
    "price": 50,
    "food": 6,
    "saturation": 0.6,
    "thirst": -2,
    "effects": [
      {
        "effect": "speed",
        "seconds": 30,
        "amplifier": 0
      },
      {
        "effect": "fire_resistance",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7มะละกอสับ ถั่วลิสง มะเขือเทศ เผ็ดจนตัวร้อน",
      "§6อิ่มท้อง §f+6",
      "§cกระหายน้ำ §f-2 §7(เผ็ด/เค็ม)",
      "§dวิ่งเร็ว 30วิ, ทนไฟ 30วิ"
    ]
  },
  {
    "key": "somtum_pla_ra",
    "id": "food:somtum_pla_ra",
    "name": "ส้มตำปูปลาร้า",
    "price": 55,
    "food": 7,
    "saturation": 0.6,
    "thirst": -3,
    "effects": [
      {
        "effect": "strength",
        "seconds": 20,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7นัวปลาร้าแท้ แซ่บถึงใจสายอีสาน",
      "§6อิ่มท้อง §f+7",
      "§cกระหายน้ำ §f-3 §7(เผ็ด/เค็ม)",
      "§dแรงขึ้น 20วิ, วิ่งเร็ว 30วิ"
    ]
  },
  {
    "key": "larb_plate",
    "id": "food:larb_plate",
    "name": "ลาบหมู",
    "price": 60,
    "food": 8,
    "saturation": 0.7,
    "thirst": -1,
    "effects": [
      {
        "effect": "jump_boost",
        "seconds": 30,
        "amplifier": 0
      },
      {
        "effect": "resistance",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7หมูสับคั่วข้าวคั่ว หอมสมุนไพร",
      "§6อิ่มท้อง §f+8",
      "§cกระหายน้ำ §f-1 §7(เผ็ด/เค็ม)",
      "§dกระโดดสูง 30วิ, ทนทาน 20วิ"
    ]
  },
  {
    "key": "kratip_rice",
    "id": "food:kratip_rice",
    "name": "ข้าวเหนียว 1 กระติ๊บ",
    "price": 10,
    "food": 4,
    "saturation": 1.0,
    "thirst": -1,
    "effects": [],
    "lore": [
      "§7ข้าวเหนียวนึ่งร้อนๆ อยู่ท้องนาน",
      "§6อิ่มท้อง §f+4",
      "§cกระหายน้ำ §f-1 §7(เผ็ด/เค็ม)"
    ]
  },
  {
    "key": "kaeng_som",
    "id": "food:kaeng_som",
    "name": "แกงส้มใต้",
    "price": 70,
    "food": 8,
    "saturation": 0.7,
    "thirst": 5,
    "effects": [
      {
        "effect": "fire_resistance",
        "seconds": 45,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 6,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7น้ำแกงเหลืองจัดจ้าน เปรี้ยวเผ็ดร้อน",
      "§6อิ่มท้อง §f+8",
      "§bดับกระหาย §f+5",
      "§dทนไฟ 45วิ, ฟื้นเลือด 6วิ"
    ]
  },
  {
    "key": "omelette_rice",
    "id": "food:omelette_rice",
    "name": "ข้าวไข่เจียว สูตรผู้บัญชาการ",
    "price": 45,
    "food": 8,
    "saturation": 0.8,
    "thirst": -1,
    "effects": [
      {
        "effect": "resistance",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ไข่เจียวฟูกรอบ ราดซอสพริก อิ่มพร้อมรบ",
      "§6อิ่มท้อง §f+8",
      "§cกระหายน้ำ §f-1 §7(เผ็ด/เค็ม)",
      "§dทนทาน 30วิ"
    ]
  },
  {
    "key": "fried_chicken_bucket",
    "id": "food:fried_chicken_bucket",
    "name": "ถังไก่ทอดสูตรยายน้อย (8 ชิ้น)",
    "price": 199,
    "food": 20,
    "saturation": 1.0,
    "thirst": -2,
    "effects": [
      {
        "effect": "strength",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 10,
        "amplifier": 0
      },
      {
        "effect": "absorption",
        "seconds": 60,
        "amplifier": 1
      }
    ],
    "lore": [
      "§7ไก่ทอดหนังกรอบ 8 ชิ้น อิ่มเต็มท้อง",
      "§6อิ่มท้อง §f+20",
      "§cกระหายน้ำ §f-2 §7(เผ็ด/เค็ม)",
      "§dแรงขึ้น 60วิ, ฟื้นเลือด 10วิ, เลือดเสริม II 60วิ"
    ]
  },
  {
    "key": "spicy_chicken_bucket",
    "id": "food:spicy_chicken_bucket",
    "name": "ถังไก่ทอดซอสเผ็ดเกาหลี (8 ชิ้น)",
    "price": 219,
    "food": 20,
    "saturation": 1.0,
    "thirst": -4,
    "effects": [
      {
        "effect": "strength",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "fire_resistance",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7เคลือบซอสโคชูจังเผ็ดหวาน",
      "§6อิ่มท้อง §f+20",
      "§cกระหายน้ำ §f-4 §7(เผ็ด/เค็ม)",
      "§dแรงขึ้น 60วิ, ทนไฟ 60วิ, วิ่งเร็ว 30วิ"
    ]
  },
  {
    "key": "moo_ping",
    "id": "food:moo_ping",
    "name": "หมูปิ้งนมสด 3 ไม้ + ข้าวเหนียว",
    "price": 40,
    "food": 8,
    "saturation": 0.8,
    "thirst": -1,
    "effects": [
      {
        "effect": "speed",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7หมูหมักนมสดย่างเตาถ่าน มื้อเช้าคนไทย",
      "§6อิ่มท้อง §f+8",
      "§cกระหายน้ำ §f-1 §7(เผ็ด/เค็ม)",
      "§dวิ่งเร็ว 20วิ"
    ]
  },
  {
    "key": "ramen_bowl",
    "id": "food:ramen_bowl",
    "name": "ราเมงโชยุ สูตรท่านฮารุโตะ",
    "price": 139,
    "food": 12,
    "saturation": 0.8,
    "thirst": 6,
    "effects": [
      {
        "effect": "haste",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 8,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7น้ำซุปโชยุเคี่ยว 12 ชั่วโมง ไข่ยางมะตูม",
      "§6อิ่มท้อง §f+12",
      "§bดับกระหาย §f+6",
      "§dขุด/ทำงานไว 60วิ, ฟื้นเลือด 8วิ"
    ]
  },
  {
    "key": "tomyum_ramen",
    "id": "food:tomyum_ramen",
    "name": "ราเมงต้มยำ สูตรท่านฮารุโตะ",
    "price": 149,
    "food": 12,
    "saturation": 0.8,
    "thirst": 4,
    "effects": [
      {
        "effect": "haste",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "fire_resistance",
        "seconds": 45,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ซุปต้มยำน้ำข้น เปรี้ยวเผ็ดแบบไทย",
      "§6อิ่มท้อง §f+12",
      "§bดับกระหาย §f+4",
      "§dขุด/ทำงานไว 60วิ, ทนไฟ 45วิ, วิ่งเร็ว 20วิ"
    ]
  },
  {
    "key": "tonkotsu_ramen",
    "id": "food:tonkotsu_ramen",
    "name": "ราเมงทงคตสึ สูตรท่านฮารุโตะ",
    "price": 159,
    "food": 14,
    "saturation": 0.9,
    "thirst": 6,
    "effects": [
      {
        "effect": "haste",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "resistance",
        "seconds": 45,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 10,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ซุปกระดูกหมูข้นขาว เข้มข้นถึงใจ",
      "§6อิ่มท้อง §f+14",
      "§bดับกระหาย §f+6",
      "§dขุด/ทำงานไว 60วิ, ทนทาน 45วิ, ฟื้นเลือด 10วิ"
    ]
  },
  {
    "key": "fried_insects_plate",
    "id": "food:fried_insects_plate",
    "name": "แมลงทอดรวม สูตรท่านฮารุโตะ",
    "price": 60,
    "food": 7,
    "saturation": 0.7,
    "thirst": -2,
    "effects": [
      {
        "effect": "jump_boost",
        "seconds": 30,
        "amplifier": 1
      },
      {
        "effect": "strength",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7จิ้งหรีด หนอนรถด่วน ตั๊กแตน กรอบโปรตีนสูง",
      "§6อิ่มท้อง §f+7",
      "§cกระหายน้ำ §f-2 §7(เผ็ด/เค็ม)",
      "§dกระโดดสูง II 30วิ, แรงขึ้น 20วิ"
    ]
  },
  {
    "key": "spicy_insects_plate",
    "id": "food:spicy_insects_plate",
    "name": "แมลงทอดคลุกผงต้มยำ",
    "price": 70,
    "food": 7,
    "saturation": 0.7,
    "thirst": -3,
    "effects": [
      {
        "effect": "jump_boost",
        "seconds": 30,
        "amplifier": 1
      },
      {
        "effect": "strength",
        "seconds": 20,
        "amplifier": 0
      },
      {
        "effect": "night_vision",
        "seconds": 60,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7คลุกผงต้มยำเผ็ดๆ กรอบจนหยุดไม่ได้",
      "§6อิ่มท้อง §f+7",
      "§cกระหายน้ำ §f-3 §7(เผ็ด/เค็ม)",
      "§dกระโดดสูง II 30วิ, แรงขึ้น 20วิ, มองในที่มืด 60วิ"
    ]
  },
  {
    "key": "boba_tea",
    "id": "food:boba_tea",
    "name": "ชานมไข่มุก ฮารุโตะ",
    "price": 45,
    "food": 2,
    "saturation": 0.3,
    "thirst": 12,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 12,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ชานมหอมมัน ไข่มุกหนึบ",
      "§6อิ่มท้อง §f+2",
      "§bดับกระหาย §f+12",
      "§dฟื้นเลือด 12วิ"
    ]
  },
  {
    "key": "thai_tea_boba",
    "id": "food:thai_tea_boba",
    "name": "ชาไทยไข่มุก",
    "price": 45,
    "food": 2,
    "saturation": 0.3,
    "thirst": 12,
    "effects": [
      {
        "effect": "speed",
        "seconds": 45,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7ชาไทยสีส้มหวานมัน ดื่มแล้วคึก",
      "§6อิ่มท้อง §f+2",
      "§bดับกระหาย §f+12",
      "§dวิ่งเร็ว 45วิ"
    ]
  },
  {
    "key": "matcha_boba",
    "id": "food:matcha_boba",
    "name": "ชาเขียวมัทฉะนมไข่มุก",
    "price": 55,
    "food": 2,
    "saturation": 0.3,
    "thirst": 12,
    "effects": [
      {
        "effect": "absorption",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 8,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7มัทฉะแท้จากอุจิ หอมละมุน",
      "§6อิ่มท้อง §f+2",
      "§bดับกระหาย §f+12",
      "§dเลือดเสริม 60วิ, ฟื้นเลือด 8วิ"
    ]
  },
  {
    "key": "cocoa_boba",
    "id": "food:cocoa_boba",
    "name": "โกโก้ไข่มุก",
    "price": 50,
    "food": 3,
    "saturation": 0.4,
    "thirst": 11,
    "effects": [
      {
        "effect": "night_vision",
        "seconds": 90,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7โกโก้เข้มข้น ดื่มแล้วตาสว่าง",
      "§6อิ่มท้อง §f+3",
      "§bดับกระหาย §f+11",
      "§dมองในที่มืด 90วิ"
    ]
  },
  {
    "key": "kratom_bottle",
    "id": "food:kratom_bottle",
    "name": "น้ำชาสูตรลับจากท่านฮารุโตะ",
    "price": 89,
    "food": 2,
    "saturation": 0.3,
    "thirst": 14,
    "effects": [
      {
        "effect": "night_vision",
        "seconds": 45,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 35,
        "amplifier": 1
      },
      {
        "effect": "resistance",
        "seconds": 35,
        "amplifier": 0
      }
    ],
    "lore": [
      "§7สูตรลับเฉพาะร้าน ใครดื่มก็ฮึกเหิม",
      "§6อิ่มท้อง §f+2",
      "§bดับกระหาย §f+14",
      "§dมองในที่มืด 45วิ, วิ่งเร็ว II 35วิ, ทนทาน 35วิ"
    ]
  }
];

// GENERATED - pharmacy + convenience store goods (cure = effects removed, heal = instant health)
export const STORE_GOODS = [
  {
    "key": "med_paracetamol",
    "id": "succubi:med_paracetamol",
    "name": "พาราเซตามอล 500 มก. (1 แผง)",
    "price": 15,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 10,
    "lore": [
      "§7ลดไข้ แก้ปวด ฟื้นเลือดทันที",
      "§aฟื้นเลือดทันที §f+10",
      "§dฟื้นเลือด 20วิ"
    ]
  },
  {
    "key": "med_cough_syrup",
    "id": "succubi:med_cough_syrup",
    "name": "ยาแก้ไอน้ำดำ",
    "price": 45,
    "food": 0,
    "saturation": 0,
    "thirst": 2,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 15,
        "amplifier": 0
      }
    ],
    "cure": [
      "weakness",
      "mining_fatigue"
    ],
    "heal": 0,
    "lore": [
      "§7ชุ่มคอ หายอ่อนแรง",
      "§bดับกระหาย §f+2",
      "§dฟื้นเลือด 15วิ",
      "§eหายจาก: อ่อนแรง, เหนื่อยล้า"
    ]
  },
  {
    "key": "med_inhaler",
    "id": "succubi:med_inhaler",
    "name": "ยาดม",
    "price": 25,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [
      {
        "effect": "night_vision",
        "seconds": 60,
        "amplifier": 0
      }
    ],
    "cure": [
      "nausea",
      "blindness",
      "darkness"
    ],
    "heal": 0,
    "lore": [
      "§7สูดแล้วหายมึน ตาสว่าง",
      "§dมองในที่มืด 60วิ",
      "§eหายจาก: คลื่นไส้, ตาพร่า, มืดมัว"
    ]
  },
  {
    "key": "med_balm",
    "id": "succubi:med_balm",
    "name": "ยาหม่อง",
    "price": 35,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [
      {
        "effect": "resistance",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "cure": [
      "slowness"
    ],
    "heal": 0,
    "lore": [
      "§7ทาแล้วคลายเส้น ตัวเบา",
      "§dทนทาน 30วิ",
      "§eหายจาก: เชื่องช้า"
    ]
  },
  {
    "key": "med_plaster",
    "id": "succubi:med_plaster",
    "name": "พลาสเตอร์ปิดแผล (กล่อง)",
    "price": 20,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 5,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 6,
    "lore": [
      "§7ปิดแผลเล็ก ฟื้นเลือดเล็กน้อย",
      "§aฟื้นเลือดทันที §f+6",
      "§dฟื้นเลือด 5วิ"
    ]
  },
  {
    "key": "med_ors",
    "id": "succubi:med_ors",
    "name": "เกลือแร่ ORS (ซอง)",
    "price": 8,
    "food": 0,
    "saturation": 0,
    "thirst": 8,
    "effects": [],
    "cure": [
      "weakness"
    ],
    "heal": 0,
    "lore": [
      "§7ชงน้ำดื่ม แก้ขาดน้ำ",
      "§bดับกระหาย §f+8",
      "§eหายจาก: อ่อนแรง"
    ]
  },
  {
    "key": "med_vitamin_c",
    "id": "succubi:med_vitamin_c",
    "name": "วิตามินซี 1000 มก.",
    "price": 60,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [
      {
        "effect": "absorption",
        "seconds": 120,
        "amplifier": 0
      },
      {
        "effect": "regeneration",
        "seconds": 10,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7เสริมภูมิ ร่างกายแข็งแรง",
      "§dเลือดเสริม 120วิ, ฟื้นเลือด 10วิ"
    ]
  },
  {
    "key": "med_motion",
    "id": "succubi:med_motion",
    "name": "ยาแก้เมารถ",
    "price": 20,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [
      "nausea",
      "darkness"
    ],
    "heal": 0,
    "lore": [
      "§7หายเวียนหัว คลื่นไส้",
      "§eหายจาก: คลื่นไส้, มืดมัว"
    ]
  },
  {
    "key": "med_antacid",
    "id": "succubi:med_antacid",
    "name": "ยาธาตุน้ำขาว",
    "price": 55,
    "food": 0,
    "saturation": 0,
    "thirst": 1,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 5,
        "amplifier": 0
      }
    ],
    "cure": [
      "poison",
      "hunger",
      "nausea"
    ],
    "heal": 0,
    "lore": [
      "§7แก้ท้องอืด ถอนพิษอาหาร",
      "§bดับกระหาย §f+1",
      "§dฟื้นเลือด 5วิ",
      "§eหายจาก: พิษ, หิวโซ, คลื่นไส้"
    ]
  },
  {
    "key": "snack_peanuts",
    "id": "succubi:snack_peanuts",
    "name": "ถั่วลิสงอบเกลือ",
    "price": 20,
    "food": 4,
    "saturation": 0.5,
    "thirst": -1,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7กรอบมัน เค็มนิดๆ",
      "§6อิ่มท้อง §f+4",
      "§cกระหายน้ำ §f-1 §7(เค็ม/เผ็ด)"
    ]
  },
  {
    "key": "drink_milk",
    "id": "succubi:drink_milk",
    "name": "นมจืด UHT",
    "price": 14,
    "food": 2,
    "saturation": 0.4,
    "thirst": 8,
    "effects": [],
    "cure": [
      "poison",
      "nausea",
      "weakness",
      "slowness"
    ],
    "heal": 0,
    "lore": [
      "§7ดื่มแล้วล้างอาการแย่ๆ ออกหมด",
      "§6อิ่มท้อง §f+2",
      "§bดับกระหาย §f+8",
      "§eหายจาก: พิษ, คลื่นไส้, อ่อนแรง, เชื่องช้า"
    ]
  },
  {
    "key": "drink_m150",
    "id": "succubi:drink_m150",
    "name": "เครื่องดื่มชูกำลัง M-150",
    "price": 12,
    "food": 0,
    "saturation": 0,
    "thirst": 5,
    "effects": [
      {
        "effect": "haste",
        "seconds": 60,
        "amplifier": 0
      },
      {
        "effect": "speed",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ขวดเล็ก พลังเต็ม",
      "§bดับกระหาย §f+5",
      "§dขุด/ทำงานไว 60วิ, วิ่งเร็ว 20วิ"
    ]
  },
  {
    "key": "onigiri_tuna",
    "id": "succubi:onigiri_tuna",
    "name": "ข้าวปั้นทูน่ามายองเนส",
    "price": 25,
    "food": 5,
    "saturation": 0.6,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ข้าวญี่ปุ่นห่อสาหร่าย ไส้ทูน่า",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "onigiri_salmon",
    "id": "succubi:onigiri_salmon",
    "name": "ข้าวปั้นแซลมอน",
    "price": 35,
    "food": 6,
    "saturation": 0.6,
    "thirst": 0,
    "effects": [
      {
        "effect": "regeneration",
        "seconds": 5,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7แซลมอนย่างชิ้นโต",
      "§6อิ่มท้อง §f+6",
      "§dฟื้นเลือด 5วิ"
    ]
  },
  {
    "key": "sandwich_ham",
    "id": "succubi:sandwich_ham",
    "name": "แซนด์วิชแฮมชีส",
    "price": 29,
    "food": 5,
    "saturation": 0.6,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ขนมปังนุ่ม แฮม ชีส",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "toastie_ham",
    "id": "succubi:toastie_ham",
    "name": "แซนด์วิชอบ แฮมชีส",
    "price": 39,
    "food": 7,
    "saturation": 0.7,
    "thirst": 0,
    "effects": [
      {
        "effect": "resistance",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7อบร้อนๆ ชีสยืด",
      "§6อิ่มท้อง §f+7",
      "§dทนทาน 20วิ"
    ]
  },
  {
    "key": "dim_sum",
    "id": "succubi:dim_sum",
    "name": "ขนมจีบกุ้ง (4 ชิ้น)",
    "price": 25,
    "food": 5,
    "saturation": 0.6,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7นึ่งร้อน ราดซีอิ๊วดำ",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "bao",
    "id": "succubi:bao",
    "name": "ซาลาเปาหมูสับ",
    "price": 20,
    "food": 5,
    "saturation": 0.7,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7แป้งนุ่ม ไส้แน่น",
      "§6อิ่มท้อง §f+5"
    ]
  },
  {
    "key": "sausage",
    "id": "succubi:sausage",
    "name": "ไส้กรอกจัมโบ้",
    "price": 35,
    "food": 6,
    "saturation": 0.6,
    "thirst": -1,
    "effects": [
      {
        "effect": "strength",
        "seconds": 20,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ย่างร้อนๆ จากตู้",
      "§6อิ่มท้อง §f+6",
      "§cกระหายน้ำ §f-1 §7(เค็ม/เผ็ด)",
      "§dแรงขึ้น 20วิ"
    ]
  },
  {
    "key": "rice_krapow",
    "id": "succubi:rice_krapow",
    "name": "ข้าวกะเพราไก่ไข่ดาว (กล่อง)",
    "price": 45,
    "food": 10,
    "saturation": 0.8,
    "thirst": -2,
    "effects": [
      {
        "effect": "strength",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7เวฟร้อน เผ็ดจัดจ้าน",
      "§6อิ่มท้อง §f+10",
      "§cกระหายน้ำ §f-2 §7(เค็ม/เผ็ด)",
      "§dแรงขึ้น 30วิ"
    ]
  },
  {
    "key": "rice_garlic_pork",
    "id": "succubi:rice_garlic_pork",
    "name": "ข้าวหมูทอดกระเทียม (กล่อง)",
    "price": 49,
    "food": 10,
    "saturation": 0.8,
    "thirst": -1,
    "effects": [
      {
        "effect": "resistance",
        "seconds": 30,
        "amplifier": 0
      }
    ],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7หมูทอดกรอบ กระเทียมเจียว",
      "§6อิ่มท้อง §f+10",
      "§cกระหายน้ำ §f-1 §7(เค็ม/เผ็ด)",
      "§dทนทาน 30วิ"
    ]
  },
  {
    "key": "boiled_eggs",
    "id": "succubi:boiled_eggs",
    "name": "ไข่ต้ม (แพ็ค 2 ฟอง)",
    "price": 12,
    "food": 4,
    "saturation": 0.8,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7โปรตีนง่ายๆ อิ่มนาน",
      "§6อิ่มท้อง §f+4"
    ]
  },
  {
    "key": "teddy_bear",
    "id": "succubi:teddy_bear",
    "name": "ตุ๊กตาหมีกอดคลายเครียด",
    "price": 99,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7คลิกขวากอดเพื่อเพิ่มสติ +12 (ทุก 90 วินาที) ใช้ได้ไม่จำกัด"
    ]
  },
  {
    "key": "book_newspaper",
    "id": "succubi:book_newspaper",
    "name": "หนังสือพิมพ์รายวัน",
    "price": 20,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ข่าวรอบเซิร์ฟ อ่านจบแล้วทิ้ง §7(อ่านจบ: สติ +3)"
    ],
    "short": "หนังสือพิมพ์"
  },
  {
    "key": "book_comic",
    "id": "succubi:book_comic",
    "name": "การ์ตูนแก๊กขำกลิ้ง",
    "price": 65,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7หัวเราะจนลืมกลัว §7(อ่านจบ: สติ +10, คูลดาวน์ 10 นาที)"
    ],
    "short": "การ์ตูนแก๊ก"
  },
  {
    "key": "book_travel",
    "id": "succubi:book_travel",
    "name": "นิตยสารเที่ยวทั่วไทย",
    "price": 89,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ภาพทะเล ภูเขา อ่านแล้วใจฟู §7(อ่านจบ: สติ +8, คูลดาวน์ 10 นาที)"
    ],
    "short": "นิตยสารเที่ยว"
  },
  {
    "key": "book_romance",
    "id": "succubi:book_romance",
    "name": "นิยายรัก 'ใต้แสงจันทร์'",
    "price": 259,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7หวานจนลืมความมืด §7(อ่านจบ: สติ +15, คูลดาวน์ 20 นาที)"
    ],
    "short": "นิยายรัก"
  },
  {
    "key": "book_mystery",
    "id": "succubi:book_mystery",
    "name": "นิยายสืบสวน 'คดีบ้านร้าง'",
    "price": 289,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ลุ้นจนวางไม่ลง §7(อ่านจบ: สติ +15, คูลดาวน์ 20 นาที)"
    ],
    "short": "นิยายสืบสวน"
  },
  {
    "key": "book_dharma",
    "id": "succubi:book_dharma",
    "name": "หนังสือธรรมะ 'ใจสงบ'",
    "price": 99,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7อ่านจบแล้วไม่หวั่นคำสาปตุ๊กตา 30 นาที §7(อ่านจบ: สติ +20, คูลดาวน์ 30 นาที)"
    ],
    "short": "หนังสือธรรมะ"
  },
  {
    "key": "book_prayer",
    "id": "succubi:book_prayer",
    "name": "หนังสือสวดมนต์",
    "price": 35,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7อ่านจบแล้วกันเหตุการณ์ผิดปกติครั้งถัดไป §7(อ่านจบ: สติ +6, คูลดาวน์ 10 นาที)"
    ],
    "short": "สวดมนต์"
  },
  {
    "key": "book_coloring",
    "id": "succubi:book_coloring",
    "name": "สมุดระบายสี + สีเทียน",
    "price": 45,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ระบายสีเพลินๆ คลายเครียด §7(อ่านจบ: สติ +8, คูลดาวน์ 10 นาที)"
    ],
    "short": "สมุดระบายสี"
  },
  {
    "key": "book_survival",
    "id": "succubi:book_survival",
    "name": "คู่มือเอาชีวิตรอดฉบับพกพา",
    "price": 199,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7สรุประบบของเซิร์ฟ อ่านแล้วอุ่นใจ §7(อ่านจบ: สติ +5, คูลดาวน์ 5 นาที)"
    ],
    "short": "คู่มือรอด"
  },
  {
    "key": "book_ghost",
    "id": "succubi:book_ghost",
    "name": "หนังสือเล่มดำ 'เรื่องเล่าต้องห้าม'",
    "price": 159,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7§cอย่าอ่านคนเดียว... สติลด และเจอเรื่องแปลก §7(อ่านจบ: สติ -10, คูลดาวน์ 15 นาที)"
    ],
    "short": "เล่มดำ"
  },
  {
    "key": "amulet_luang_por",
    "id": "succubi:amulet_luang_por",
    "name": "พระเครื่องหลวงพ่อ",
    "price": 1299,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ฟื้นเลือด +1 ทุก 4 วินาที §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "พระหลวงพ่อ"
  },
  {
    "key": "amulet_takrut",
    "id": "succubi:amulet_takrut",
    "name": "ตะกรุดโทน",
    "price": 899,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7สติฟื้นเอง +3/นาที, เรื่องแปลกเสียสติน้อยลง 30% §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "ตะกรุดโทน"
  },
  {
    "key": "amulet_bia_kae",
    "id": "succubi:amulet_bia_kae",
    "name": "เบี้ยแก้",
    "price": 699,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ล้างพิษ คลื่นไส้ และอาการเหี่ยวเฉาเองอัตโนมัติ §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "เบี้ยแก้"
  },
  {
    "key": "amulet_pha_yant",
    "id": "succubi:amulet_pha_yant",
    "name": "ผ้ายันต์ห้าแถว",
    "price": 1599,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ทนทาน (Resistance I) ตลอดเวลา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "ผ้ายันต์"
  },
  {
    "key": "amulet_khiao_suea",
    "id": "succubi:amulet_khiao_suea",
    "name": "เขี้ยวเสือ",
    "price": 1199,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7วิ่งเร็ว (Speed I) ตลอดเวลา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "เขี้ยวเสือ"
  },
  {
    "key": "amulet_nang_kwak",
    "id": "succubi:amulet_nang_kwak",
    "name": "นางกวัก",
    "price": 999,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ลดราคาทุกร้าน 10% §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "นางกวัก"
  },
  {
    "key": "amulet_kuman_thong",
    "id": "succubi:amulet_kuman_thong",
    "name": "กุมารทอง",
    "price": 2499,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ทุก 15 นาทีได้เงินสด 10-60 บาท §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "กุมารทอง"
  },
  {
    "key": "amulet_ta_thip",
    "id": "succubi:amulet_ta_thip",
    "name": "ตาทิพย์",
    "price": 799,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7มองในที่มืด (Night Vision) ตลอดเวลา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "ตาทิพย์"
  },
  {
    "key": "amulet_cursed_doll",
    "id": "succubi:amulet_cursed_doll",
    "name": "ตุ๊กตาสาปแช่ง",
    "price": 666,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7คนรอบตัว 20 บล็อกเจอเรื่องแปลกเร็วขึ้น 2 เท่า (ผู้ใส่เสียสติช้าๆ) §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "ตุ๊กตาสาป"
  },
  {
    "key": "amulet_yant_kan_phi",
    "id": "succubi:amulet_yant_kan_phi",
    "name": "ยันต์กันผี",
    "price": 1499,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7เรื่องแปลกช้าลงครึ่งหนึ่ง เสียสติน้อยลงครึ่ง กันคำสาปตุ๊กตา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "ยันต์กันผี"
  },
  {
    "key": "amulet_lek_lai",
    "id": "succubi:amulet_lek_lai",
    "name": "เหล็กไหล",
    "price": 1799,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ทนไฟ (Fire Resistance) ตลอดเวลา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "เหล็กไหล"
  },
  {
    "key": "amulet_moon",
    "id": "succubi:amulet_moon",
    "name": "ลูกแก้วจันทรา",
    "price": 1099,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7กลางคืนสติฟื้นเอง +6/นาที §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "แก้วจันทรา"
  },
  {
    "key": "amulet_hanuman",
    "id": "succubi:amulet_hanuman",
    "name": "หนุมานเชิญธง",
    "price": 1999,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7แรงขึ้น (Strength I) ตลอดเวลา §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "หนุมาน"
  },
  {
    "key": "amulet_mae_pho",
    "id": "succubi:amulet_mae_pho",
    "name": "แม่โพสพ",
    "price": 599,
    "food": 0,
    "saturation": 0,
    "thirst": 0,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7อิ่มนาน: เติมความอิ่มนิดหน่อยทุกนาที §7(ใส่ในกระเป๋าตังค์ > เครื่องราง)"
    ],
    "short": "แม่โพสพ"
  },
  {
    "key": "snack_chips_nori",
    "id": "succubi:snack_chips_nori",
    "name": "มันฝรั่งทอดรสสาหร่าย",
    "price": 20,
    "food": 4,
    "saturation": 0.3,
    "thirst": -1,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7กรอบ หอมสาหร่าย",
      "§6อิ่มท้อง §f+4",
      "§cกระหายน้ำ §f-1 §7(เค็ม/เผ็ด)"
    ]
  },
  {
    "key": "snack_chips_bbq",
    "id": "succubi:snack_chips_bbq",
    "name": "มันฝรั่งทอดรสบาร์บีคิว (ถุงใหญ่)",
    "price": 33,
    "food": 6,
    "saturation": 0.3,
    "thirst": -2,
    "effects": [],
    "cure": [],
    "heal": 0,
    "lore": [
      "§7ถุงใหญ่ รสเข้มข้น",
      "§6อิ่มท้อง §f+6",
      "§cกระหายน้ำ §f-2 §7(เค็ม/เผ็ด)"
    ]
  }
];

export const PRODUCT_BY_ID = new Map([...DRINKS, ...SNACKS, ...KIOSK_FOODS, ...STORE_GOODS].map((p) => [p.id, p]));

// sanity line in every product description
for (const p of PRODUCT_BY_ID.values()) {
  const s = SANITY_BY_ID[p.id];
  if (s && !p.lore.some((l) => l.includes("สติ"))) p.lore = [...p.lore, s > 0 ? `§5สติ §f+${s}` : `§4สติ §f${s}`];
}

// Server medical items the pharmacy also sells (their own scripts handle them)
const MEDICAL = {
  "kotarus:bandage_blackpowder": { key: "bandage_blackpowder", name: "ผ้าพันแผลธรรมดา" },
  "kotarus:syringe_blackpowder": { key: "syringe_blackpowder", name: "ยาลดไข้ (เข็มฉีด)" },
  "kotarus:medkit_blackpowder": { key: "medkit_blackpowder", name: "อุปกรณ์ชุบชีวิต" }
};


// Shop menu = product + the price that shop charges (vending drinks cost a little more at a stall)
const SHORT_NAMES = {
  "food:somtum_plate": "ส้มตำไทย",
  "food:somtum_pla_ra": "ตำปูปลาร้า",
  "food:larb_plate": "ลาบหมู",
  "food:kratip_rice": "ข้าวเหนียว",
  "food:kaeng_som": "แกงส้มใต้",
  "food:omelette_rice": "ข้าวไข่เจียว",
  "food:fried_chicken_bucket": "ถังไก่ทอด",
  "food:spicy_chicken_bucket": "ไก่ซอสเกาหลี",
  "food:moo_ping": "หมูปิ้ง+ข้าว",
  "food:ramen_bowl": "ราเมงโชยุ",
  "food:tomyum_ramen": "ราเมงต้มยำ",
  "food:tonkotsu_ramen": "ราเมงทงคตสึ",
  "food:fried_insects_plate": "แมลงทอด",
  "food:spicy_insects_plate": "แมลงต้มยำ",
  "food:boba_tea": "ชานมไข่มุก",
  "food:thai_tea_boba": "ชาไทยไข่มุก",
  "food:matcha_boba": "มัทฉะไข่มุก",
  "food:cocoa_boba": "โกโก้ไข่มุก",
  "food:kratom_bottle": "ชาสูตรลับ",
  "succubi:med_paracetamol": "พาราเซตามอล",
  "succubi:med_cough_syrup": "ยาแก้ไอ",
  "succubi:med_inhaler": "ยาดม",
  "succubi:med_balm": "ยาหม่อง",
  "succubi:med_plaster": "พลาสเตอร์",
  "succubi:med_ors": "เกลือแร่ ORS",
  "succubi:med_vitamin_c": "วิตามินซี",
  "succubi:med_motion": "ยาแก้เมารถ",
  "succubi:med_antacid": "ยาธาตุ",
  "kotarus:bandage_blackpowder": "ผ้าพันแผล",
  "kotarus:syringe_blackpowder": "เข็มลดไข้",
  "kotarus:medkit_blackpowder": "ชุดชุบชีวิต",
  "succubi:snack_peanuts": "ถั่วอบเกลือ",
  "succubi:drink_milk": "นมจืด",
  "succubi:drink_m150": "M-150",
  "succubi:onigiri_tuna": "ข้าวปั้นทูน่า",
  "succubi:onigiri_salmon": "ปั้นแซลมอน",
  "succubi:sandwich_ham": "แซนด์วิช",
  "succubi:toastie_ham": "แซนด์วิชอบ",
  "succubi:dim_sum": "ขนมจีบ",
  "succubi:bao": "ซาลาเปา",
  "succubi:sausage": "ไส้กรอก",
  "succubi:rice_krapow": "ข้าวกะเพรา",
  "succubi:rice_garlic_pork": "หมูกระเทียม",
  "succubi:boiled_eggs": "ไข่ต้ม",
  "succubi:teddy_bear": "ตุ๊กตาหมี",
  "succubi:snack_chips_nori": "มันฯสาหร่าย",
  "succubi:snack_chips_bbq": "มันฯบาร์บีคิว",
  "succubi:drink_water_bottle": "น้ำดื่ม",
  "succubi:drink_pepsi": "เป๊ปซี่",
  "succubi:drink_fanta_orange": "แฟนต้า",
  "succubi:drink_sprite": "สไปรท์",
  "succubi:drink_coca_cola": "โค้ก",
  "succubi:drink_schweppes": "ชเวปส์",
  "succubi:drink_boss_coffee": "กาแฟกระป๋อง",
  "succubi:drink_pocari_sweat": "โพคารี่",
  "succubi:drink_redbull": "เรดบูล",
  "succubi:drink_green_tea": "ชาเขียว",
  "succubi:drink_monster_energy": "มอนสเตอร์",
  "succubi:snack_wafer": "เวเฟอร์",
  "succubi:snack_jelly": "เยลลี่",
  "succubi:snack_prawn_crackers": "ข้าวเกรียบ",
  "succubi:snack_cream_bun": "ขนมปังครีม",
  "succubi:snack_chips": "มันฝรั่ง",
  "succubi:snack_fish_strips": "ปลาเส้น",
  "succubi:snack_cookies": "คุกกี้",
  "succubi:snack_biscuit_sticks": "บิสกิตแท่ง",
  "succubi:snack_seaweed": "สาหร่าย",
  "succubi:snack_chocolate": "ช็อกโกแลต",
  "succubi:snack_chips_tube": "มันฯกระป๋อง"
};

const menu = (entries) =>
  entries.map(([id, price]) => {
    const p = PRODUCT_BY_ID.get(id) ?? { ...MEDICAL[id], id, lore: [] };
    return { ...p, short: SHORT_NAMES[id] ?? p.short ?? p.name, price: price ?? p.price };
  });
export const SHOP_MENUS = {
  somtum: menu([["food:somtum_plate", 50], ["food:somtum_pla_ra", 55], ["food:larb_plate", 60], ["food:kratip_rice", 10], ["succubi:drink_water_bottle", 10]]),
  chicken: menu([["food:fried_chicken_bucket", 199], ["food:spicy_chicken_bucket", 219], ["food:moo_ping", 40], ["food:kratip_rice", 10], ["succubi:drink_coca_cola", 20], ["succubi:drink_water_bottle", 10]]),
  ramen: menu([["food:ramen_bowl", 139], ["food:tomyum_ramen", 149], ["food:tonkotsu_ramen", 159], ["succubi:drink_green_tea", 35], ["succubi:drink_water_bottle", 10]]),
  omelette: menu([["food:omelette_rice", 45], ["food:kaeng_som", 70], ["food:kratip_rice", 10], ["succubi:drink_boss_coffee", 25], ["succubi:drink_pepsi", 20], ["succubi:drink_water_bottle", 10]]),
  fried_insects: menu([["food:fried_insects_plate", 60], ["food:spicy_insects_plate", 70], ["food:kratip_rice", 10], ["succubi:drink_redbull", 25], ["succubi:drink_sprite", 20], ["succubi:drink_water_bottle", 10]]),
  haruto_tea: menu([["food:boba_tea", 45], ["food:thai_tea_boba", 45], ["food:matcha_boba", 55], ["food:cocoa_boba", 50], ["food:kratom_bottle", 89], ["succubi:drink_green_tea", 35]]),
  pharmacy: menu([["succubi:med_paracetamol"], ["succubi:med_cough_syrup"], ["succubi:med_inhaler"], ["succubi:med_balm"], ["succubi:med_plaster"], ["succubi:med_ors"], ["succubi:med_vitamin_c"], ["succubi:med_motion"], ["succubi:med_antacid"], ["kotarus:bandage_blackpowder", 35], ["kotarus:syringe_blackpowder", 150], ["kotarus:medkit_blackpowder", 590]]),
  seven_snack: menu([["succubi:snack_wafer"], ["succubi:snack_jelly"], ["succubi:snack_prawn_crackers"], ["succubi:snack_cream_bun"], ["succubi:snack_chips"], ["succubi:snack_chips_nori"], ["succubi:snack_chips_bbq"], ["succubi:snack_fish_strips"], ["succubi:snack_cookies"], ["succubi:snack_biscuit_sticks"], ["succubi:snack_seaweed"], ["succubi:snack_chocolate"], ["succubi:snack_chips_tube"], ["succubi:snack_peanuts"], ["succubi:teddy_bear"]]),
  seven_drink: menu([["succubi:drink_water_bottle"], ["succubi:drink_m150"], ["succubi:drink_milk"], ["succubi:drink_pepsi"], ["succubi:drink_fanta_orange"], ["succubi:drink_sprite"], ["succubi:drink_coca_cola"], ["succubi:drink_schweppes"], ["succubi:drink_boss_coffee"], ["succubi:drink_pocari_sweat"], ["succubi:drink_redbull"], ["succubi:drink_green_tea"], ["succubi:drink_monster_energy"]]),
  seven_hot: menu([["succubi:onigiri_tuna"], ["succubi:onigiri_salmon"], ["succubi:sandwich_ham"], ["succubi:toastie_ham"], ["succubi:dim_sum"], ["succubi:bao"], ["succubi:sausage"], ["succubi:rice_krapow"], ["succubi:rice_garlic_pork"], ["succubi:boiled_eggs"]]),
  books: menu([["succubi:book_newspaper"], ["succubi:book_comic"], ["succubi:book_travel"], ["succubi:book_romance"], ["succubi:book_mystery"], ["succubi:book_dharma"], ["succubi:book_prayer"], ["succubi:book_coloring"], ["succubi:book_survival"], ["succubi:book_ghost"]]),
  amulets: menu([["succubi:amulet_luang_por"], ["succubi:amulet_takrut"], ["succubi:amulet_bia_kae"], ["succubi:amulet_pha_yant"], ["succubi:amulet_khiao_suea"], ["succubi:amulet_nang_kwak"], ["succubi:amulet_kuman_thong"], ["succubi:amulet_ta_thip"], ["succubi:amulet_cursed_doll"], ["succubi:amulet_yant_kan_phi"], ["succubi:amulet_lek_lai"], ["succubi:amulet_moon"], ["succubi:amulet_hanuman"], ["succubi:amulet_mae_pho"]])
};
