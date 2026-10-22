# เทวะมรรค (Deva Path / Six Paths of Pain) — Origin สำหรับ Minecraft 1.20.1 Forge

Origin แรงบันดาลใจจากเพน (Nagato) ใน Naruto Shippuden สำหรับม็อด **Origins** บน **Minecraft Java 1.20.1 + Forge 47.x**
ประกอบด้วย 5 เทคนิค: ชินระ เท็นเซ (ปกติ/ขั้นสูงสุด), บันโช เท็นอิน, จิบาคุ เท็นเซ, สนามแรงโน้มถ่วงรินเนกัน (พาสซีฟ) และการป้องกันสากล
พร้อมพาร์ติเคิลแบบกำหนดเอง 6 ชนิด (PNG โปร่งใสจริง), เสียง, ไฟล์ตั้งค่า และคู่มือนี้

> ## สถานะที่ต้องอ่านก่อน (ตามจริง)
>
> | สิ่งที่ทำแล้ว | สิ่งที่ **ยังไม่ได้ทำ** (ทำในเครื่องที่สร้างโปรเจกต์นี้ไม่ได้) |
> |---|---|
> | เขียนโค้ด/ทรัพยากรครบ ตรวจ syntax ด้วย `javac`, ตรวจชื่อ API เทียบกับซอร์สจริง, ตรวจ JSON/ทรัพยากรด้วยสคริปต์ | **ยังไม่เคยรัน `./gradlew build`** (เครือข่ายของเครื่องสร้างบล็อก Maven ของ Forge/Mojang) |
> | | **ยังไม่เคยคอมไพล์เทียบกับ Minecraft/Forge จริง** — จึง **ไม่มีไฟล์ `.jar` แนบมา** |
> | | **ยังไม่เคยเปิดเกมทดสอบ** (ไม่ว่าเซิร์ฟเวอร์เดี่ยว เซิร์ฟเวอร์ dedicated หรือมัลติเพลเยอร์) |
> | | ตัวตรวจโค้ดอิสระ (subagent) ถูกตัดด้วยโควตา API สามรอบ **จึงไม่มีผลรีวิวอิสระ** |
>
> ผู้ใช้ต้อง build เองหนึ่งครั้ง (ขั้นตอนอยู่ข้อ 3) แล้วทดสอบตามรายการข้อ 12 ถ้า build ไม่ผ่านหรือเกมแครช
> ให้ส่งข้อความ error มา — โค้ดทั้งหมดยังไม่เคยถูกคอมไพล์เทียบกับ Minecraft จริง จึงเป็นไปได้ที่จะมีชื่อเมธอด/ซิกเนเจอร์ผิดที่เครื่องมือตรวจแบบสแตติกมองไม่เห็น

---

## 1. สิ่งที่ต้องมี (Dependencies)

| รายการ | เวอร์ชัน | หมายเหตุ |
|---|---|---|
| Minecraft Java | **1.20.1** | |
| Forge | **47.x** (คอมไพล์กับ 47.3.0; ใช้ได้กับ 47.x ใดก็ได้ตาม `forge_version_range=[47,)`) | |
| **Origins (Forge)** | **1.20.1-1.10.0.9** | จำเป็น (`mandatory=true`) |
| **Apoli (Forge)** | **1.20.1-2.9.0.8** | จำเป็น — Origins ต้องใช้อยู่แล้ว |
| **Calio (Forge)** | **1.20.1-1.11.0.5** | จำเป็น — Origins ต้องใช้อยู่แล้ว |
| Java | **17** | สำหรับ build และรันเกม |

- `mods.toml` ประกาศ `origins ≥ 1.20.1-1.10`, `apoli ≥ 1.20.1-2.9`, `calio ≥ 1.20.1-1.11` (ตรวจกับ `mods.toml` ของ Origins ที่แจกจริงแล้ว: Origins ขึ้นกับ forge, minecraft, calio, apoli เท่านั้น)
- ม็อดนี้ **ไม่มี compile-time dependency กับ Origins/Apoli** — พาวเวอร์เป็น JSON ล้วน เรียกโค้ด Java ผ่านคำสั่ง `/painorigin ...`
- **ต้องติดตั้งทั้งฝั่งไคลเอนต์และเซิร์ฟเวอร์** (ไคลเอนต์ใช้วาดพาร์ติเคิล/เขย่ากล้อง/เสียง เซิร์ฟเวอร์ใช้รันเทคนิค)

## 2. ใครทำอะไร (JSON กับ Java)

| ส่วน | ทำด้วย | เหตุผล |
|---|---|---|
| Shinra Tensei, Massive Shinra Tensei (แรงผลัก/ดาเมจ/คูลดาวน์/ค่าจักระ) | **JSON** (Apoli `active_self` + `area_of_effect` + `add_velocity`) | JSON ทำได้เองทั้งหมด |
| Banshō Ten'in | **JSON** (`raycast` + `add_velocity`) | เลือกเป้าด้วย raycast แบบ `shape_type: collider` ที่ **หยุดเมื่อชนบล็อก** จึงไม่เลือกเป้าหลังสิ่งกีดขวาง |
| จักระ, ชาร์จป้องกัน, สนามแรงโน้มถ่วง, ตกช้า, เลือดลด | **JSON** | resource / action_over_time / modify_falling / attribute |
| การป้องกันสากล | **JSON** (`modify_damage_taken` + resource) | |
| พาร์ติเคิล 6 ชนิด, เขย่ากล้อง | **Java (ไคลเอนต์)** | JSON สร้าง particle type ใหม่/วาดแบบกำหนดเองไม่ได้ |
| เสียง 8 อีเวนต์ | **Java** (ลงทะเบียน `SoundEvent`) + `sounds.json` | |
| จิบาคุ เท็นเซ (6 เฟส, สถานะต่อผู้ใช้, ยกเลิกเมื่อตาย/ออกเกม/ข้ามมิติ) | **Java (เซิร์ฟเวอร์)** | JSON เก็บสถานะแบบหลายเฟสต่อเนื่องพร้อมยกเลิกอัตโนมัติไม่ได้ |
| การทำลายบล็อกแบบมีขีดจำกัด + เช็กสิทธิ์/บล็อกห้ามแตะ | **Java (เซิร์ฟเวอร์)** | ต้องยิง `BlockEvent.BreakEvent` และเช็กความแข็ง/blacklist |

## 3. วิธี Build และติดตั้ง

### 3.1 Build (ครั้งเดียว)
ต้องมี JDK 17 และอินเทอร์เน็ต (ดาวน์โหลด Gradle 8.8, ForgeGradle, Minecraft/Forge ครั้งแรกใช้เวลาหลายนาที)

```bash
# Linux / macOS
chmod +x gradlew
./gradlew build

# Windows
gradlew.bat build
```

ผลลัพธ์: `build/libs/painorigin-1.0.0.jar`

ถ้า `gradlew` ใช้ไม่ได้ (ไฟล์ `gradle/wrapper/gradle-wrapper.jar` เป็น wrapper มาตรฐาน ตรวจแล้วเป็นไฟล์ jar ที่เปิดได้ แต่ **ยังไม่เคยรันจริง**) ให้ติดตั้ง Gradle 8.8 เองแล้วรัน `gradle build` ในโฟลเดอร์นี้แทน

ไม่อยากติดตั้งอะไรเลย: อัปโหลดโฟลเดอร์ขึ้น GitHub — ไฟล์ `.github/workflows/build.yml` จะ build ให้ด้วย Java 17 แล้วแนบ jar เป็น artifact (**ไม่เคยถูกรันจริงเช่นกัน**)

### 3.2 ติดตั้ง
1. ติดตั้ง Minecraft 1.20.1 + Forge 47.x
2. ใส่ลงโฟลเดอร์ `mods/` (ทั้งไคลเอนต์ **และ** เซิร์ฟเวอร์): `painorigin-1.0.0.jar`, Origins, Apoli, Calio ตามเวอร์ชันในข้อ 1
3. เปิดเกม สร้างโลก/เข้าเซิร์ฟเวอร์

### 3.3 เลือก Origin
- ผู้เล่นใหม่/หลังใช้ Orb of Origin จะมีหน้าจอเลือก Origin → เลือก **เทวะมรรค (เพน)**
- หรือแอดมินสั่ง: `/origin set <ผู้เล่น> origins:origin painorigin:deva_path`
- ไฟล์ที่ผูก: `data/painorigin/origins/deva_path.json` (order 20, impact 3, ไอคอน ender_eye) และ `data/origins/origin_layers/origin.json` (เพิ่ม Origin นี้เข้า layer `origins:origin`)

## 4. ปุ่มควบคุม

| ปุ่ม | ค่าเริ่มต้น | หมายเหตุ |
|---|---|---|
| **ปุ่มหลัก** (`key.origins.primary_active`) | **G** | |
| **ปุ่มรอง** (`key.origins.secondary_active`) | **ไม่มีปุ่มเริ่มต้น** | **ต้องตั้งเอง** ที่ ตัวเลือก → การควบคุม → หมวด Origins (ข้อความนี้ขึ้นแสดงในเกมตอนเลือก Origin ด้วย) |
| Shift | ปุ่มย่อ (Sneak) | ใช้คู่กับปุ่มหลัก/รองเพื่อเลือกเทคนิคขั้นสูง |

| กด | เทคนิค |
|---|---|
| ปุ่มหลัก | ชินระ เท็นเซ |
| Shift + ปุ่มหลัก | ชินระ เท็นเซ ขั้นสูงสุด |
| ปุ่มรอง | บันโช เท็นอิน |
| Shift + ปุ่มรอง | จิบาคุ เท็นเซ |

## 5. ตารางเทคนิค (ค่าเริ่มต้น)

พลังจักระสูงสุด **100** ฟื้นฟู 1 หน่วยทุก 10 ติ๊ก (≈ 2 หน่วย/วินาที) แสดงเป็นแถบ HUD
(20 ติ๊ก = 1 วินาที)

| เทคนิค | จักระ | คูลดาวน์ | ผลหลัก (ค่าเริ่มต้น) |
|---|---|---|---|
| ชินระ เท็นเซ | 10 | 100 ติ๊ก (5 วิ) | ผลักทุกสิ่งมีชีวิตในทรงกลมรัศมี **10** บล็อก แรงแนวนอน 1.6 แนวตั้ง 0.55 ดาเมจ 3.0 **ไม่ทำลายบล็อก** |
| ชินระ เท็นเซ ขั้นสูงสุด | 40 | 1200 ติ๊ก (60 วิ) | ชาร์จ 30 ติ๊ก (1.5 วิ) แล้วผลักรัศมี **24** บล็อก แรง 3.2 / 0.9 ดาเมจ 12.0; ทำลายบล็อก **ปิดไว้** (เปิดได้ที่คอนฟิกเซิร์ฟเวอร์) |
| บันโช เท็นอิน | 8 | 80 ติ๊ก (4 วิ) | ดึงสิ่งมีชีวิตที่มองอยู่ (ไกลสุด **32** บล็อก) เข้าหาตัว แรง 1.6 / 0.4 เลือกเป้าหลังกำแพงไม่ได้ |
| จิบาคุ เท็นเซ | 80 | 3600 ติ๊ก (3 นาที) | ดูข้อ 7 |
| สนามแรงโน้มถ่วงรินเนกัน (พาสซีฟ) | — | — | ดูดไอเท็มและก้อน XP ในรัศมี **6** บล็อกเข้าหาตัว (ทุก 5 ติ๊ก แรง 0.12) |
| การป้องกันสากล (พาสซีฟ) | 5 ต่อครั้ง | ชาร์จ +1 ทุก 400 ติ๊ก (20 วิ) | สูงสุด **3 ชาร์จ** ดูข้อ 6 |
| ร่างกายอ่อนแอ (ข้อเสีย) | — | — | พลังชีวิตสูงสุด −4 (2 หัวใจ) |
| ความเข้ากันกับแรงโน้มถ่วง | — | — | ตกช้าลง 25% |

เงื่อนไขทั่วไป: ถ้าจักระไม่พอจะมีข้อความ "จักระไม่พอ"; ถ้าไม่มีเป้าหมายสำหรับ Ten'in มีข้อความ "ไม่มีเป้าหมายในสายตา" (พาวเวอร์ `notice_*`, หน่วงข้อความ 30 ติ๊ก)
ผู้เล่นโหมด Spectator ไม่ถูกผลัก/ดึง

## 6. การป้องกันสากล (Universal Defense) — เงื่อนไขและข้อจำกัด

- ใช้ **1 ชาร์จ + 5 จักระ** ต่อการป้องกัน 1 ครั้ง; ต้องมีทั้งสองอย่าง
- ยกเลิกดาเมจที่มาจาก **กระสุน (projectile), การระเบิด, หรือมีผู้โจมตี (attacker)** เท่านั้น และดาเมจต้อง > 0
- **ป้องกันไม่ได้**: ตกจากที่สูง, จมน้ำ, ไฟ/ลาวา, เวทมนตร์/ยาพิษ, ความหิว, ตกโลก (out of world) — ตั้งใจให้ไม่ใช่อมตะ
- สูงสุด 3 ชาร์จ ได้คืน 1 ชาร์จทุก 20 วินาที (ติด `defense_regen`)
- เมื่อป้องกันสำเร็จจะมีเอฟเฟกต์/เสียง และผลักผู้โจมตีที่อยู่ใกล้ (ภายใน 5 บล็อก) ออกเล็กน้อย

## 7. จิบาคุ เท็นเซ (Chibaku Tensei) — ทำงานอย่างไร

JSON หักจักระ + เริ่มคูลดาวน์ แล้วเรียก `/painorigin chibaku start` ให้ Java รันเฟสต่อเนื่อง (ตามสัดส่วนของ `chibaku.durationTicks`, ค่าเริ่มต้น 240 ติ๊ก = 12 วินาที)

| เฟส | ช่วง | เกิดอะไรขึ้น |
|---|---|---|
| 1. Activation | 0–10% | ผู้ใช้รวมพลัง กระแสออร่าหมุนรอบตัว |
| 2. Core | 10–25% | แกนมืดปรากฏเหนือผู้ใช้ `coreHeight` (14) บล็อก แล้วเริ่มโตขึ้น |
| 3. Gravity field | 25–55% | สนามแรงโน้มถ่วงรัศมี `fieldRadius` (20) ดึงสิ่งมีชีวิตเข้าหาแกน |
| 4. Debris | 55–80% | เศษหิน "บิน" เข้าแกน; สิ่งมีชีวิตถูกยกขึ้น |
| 5. Formation | 80–100% | แกนกลายเป็นก้อนหินคล้ายดาวเทียม สิ่งมีชีวิตที่ถูกจับถูกตรึงไว้ |
| 6. Final | ที่ `durationTicks` | ถล่ม: ดาเมจ (16) + แรงผลักออก (1.4), ปล่อยทุกคน, (ถ้าเปิด `realBlocks`) ลบบล็อกจริง |

**ข้อจำกัดและความปลอดภัย (ตั้งใจออกแบบ):**
- เศษหินเป็น **พาร์ติเคิลจำลอง (simulated)** โดยค่าเริ่มต้น: บล็อกพื้นถูกใช้เป็นแค่ "จุดเริ่มต้น" ของเศษหิน **โลกไม่เปลี่ยนแปลงเลย** (`chibaku.realBlocks=false`)
- โหมดทดลอง `realBlocks=true`: บล็อกที่เลือกไว้ถูกลบจริง **ครั้งเดียวตอนถล่มสุดท้ายเท่านั้น** (ถ้าถูกยกเลิกก่อนหน้านั้น โลกไม่เปลี่ยน) และผ่าน `BlockSafety` ก่อนทุกบล็อก
- จำนวนบล็อกสูงสุด `chibaku.maxBlocks` (64, ปรับได้ 0–512); ระยะเก็บบล็อก `blockRadius` (8)
- **ห้ามแตะ**: bedrock และบล็อกที่ไม่ทำลายได้ (ความแข็ง < 0), บล็อกแข็งเกิน `blocks.maxHardness` (10), บล็อกที่มี block entity (หีบ, สปอว์นเนอร์, บีคอน ฯลฯ), ของเหลว, อากาศ, บล็อกใน tag `painorigin:chibaku_protected` / `blocks.blacklist`, นอกขอบโลก/ชังก์ที่ไม่โหลด, และตำแหน่งที่ผู้ใช้ไม่มีสิทธิ์ (เช็กผ่าน `BlockEvent.BreakEvent` ที่ยิงในนามผู้ใช้ + `mayBuild` + ผู้ใช้ต้องไม่ใช่ Spectator; ผลเช็ก `BreakEvent` ถูกแคชต่อชังก์)
- **ยกเลิกทันที** เมื่อ: ผู้ใช้ตาย / ออกเกม / ข้ามมิติ / ห่างจากจุดเริ่มเกิน `interruptDistance` (6) / โดนดาเมจครั้งเดียว ≥ `interruptDamage` (3.0) / เซิร์ฟเวอร์ปิด
- สิ่งมีชีวิตที่ถูกยกจะไม่ตกตาย: ถูกปล่อยหลังลอยนานสุด `maxAirborneTicks` (60) และได้กันการตกจนกว่าจะลงพื้น (หรือ 10 วินาที) ดาเมจที่ได้รับคือการถล่มเท่านั้น
- จำกัดจำนวนสิ่งมีชีวิตที่ถูกจับต่อครั้ง `maxEntities` (48), จำนวนเซสชันพร้อมกันทั้งเซิร์ฟเวอร์ `maxSessions` (4); EntityType ใน tag `painorigin:chibaku_immune` (เช่น บอส) ไม่ถูกแตะ; `affectPlayers=false` ให้กระทบเฉพาะม็อบ
- ไม่กระทบ: ตัวผู้ใช้เอง, Spectator, ผู้เล่นโหมด Creative, ผู้เล่นที่ผู้ใช้ทำร้ายไม่ได้ตามกติกาเซิร์ฟเวอร์ (`canHarmPlayer` เช่น PvP ปิด), สัตว์เลี้ยงของผู้ใช้เอง, ArmorStand
- ข้อควรรู้: จักระถูกหักโดยพาวเวอร์ JSON **แม้ปิด `chibaku.enabled`** (เทคนิคจะไม่ทำอะไรแต่ยังเสียจักระ/คูลดาวน์)

## 8. ค่าที่ปรับได้อยู่ที่ไหน

ค่าแบ่งเป็น 2 ที่ ตามว่าใครเป็นคนอ่านค่านั้น:

### 8.1 ไฟล์คอนฟิก (`<โฟลเดอร์เกม หรือ เซิร์ฟเวอร์>/config/` — ไฟล์ของ Forge)

**`painorigin-common.toml`** (ลงทะเบียนเป็นคอนฟิกชนิด COMMON ของ Forge → ไฟล์อยู่ใน `config/` ของเครื่องที่รันม็อด ทั้งเซิร์ฟเวอร์และไคลเอนต์ **แต่ละเครื่องอ่านไฟล์ของตัวเอง ไม่ซิงก์กัน** — ค่าที่คุมเทคนิค/พาร์ติเคิลฝั่งเซิร์ฟเวอร์จึงต้องแก้ที่ `config/` ของเซิร์ฟเวอร์; ในโลกเดี่ยวคือ `config/` ของเกมเอง)

| ค่า | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `particles.enabled` | true | false = เซิร์ฟเวอร์ไม่ส่งพาร์ติเคิลของม็อดนี้เลย (พาวเวอร์ยังทำงาน) |
| `particles.countMultiplier` | 1.0 (0–4) | ตัวคูณจำนวนพาร์ติเคิลตกแต่ง (เส้นพลัง วังวน เศษหิน) |
| `particles.ambientAura` | true | ออร่ารินเนกันรอบผู้เล่นเทวะมรรค |
| `particles.range` | 96 | ผู้เล่นที่อยู่ไกลกว่านี้ไม่ได้รับพาร์ติเคิล |
| `particles.overrideVanillaLimit` | true | true = แสดงแม้ผู้เล่นตั้ง Particles เป็น Decreased/Minimal และเกินระยะ 32 บล็อกของ vanilla |
| `blocks.respectProtection` | true | เช็ก `BreakEvent` / สิทธิ์ก่อนลบบล็อก |
| `blocks.maxHardness` | 10 | บล็อกที่แข็งกว่านี้ไม่ถูกลบ |
| `blocks.blacklist` | [] | บล็อก/แท็กเพิ่มเติมที่ห้ามลบ |
| `massive.blockDestruction` | **false** | เปิดหลุมจากชินระ เท็นเซ ขั้นสูงสุด |
| `massive.maxBlocks` | 120 (0–1000) | เพดานบล็อกต่อครั้ง |
| `massive.blockRadius` | 6 | ระยะลบบล็อก (แรงผลักไกลกว่านี้ได้) |
| `chibaku.enabled` | true | |
| `chibaku.durationTicks` | 240 (100–1200) | **ระยะเวลาเอฟเฟกต์รวม** |
| `chibaku.fieldRadius` | 20 | **ขนาดสนามแรงโน้มถ่วง/ระยะถล่ม** |
| `chibaku.coreHeight` | 14 | ความสูงแกน |
| `chibaku.maxBlocks` | 64 | **จำนวนบล็อกสูงสุดของจิบาคุ** |
| `chibaku.realBlocks` | **false** | ทดลอง: ลบบล็อกจริงตอนถล่ม |
| `chibaku.blockRadius` | 8 | |
| `chibaku.damage` / `knockback` | 16 / 1.4 | ดาเมจและแรงผลักตอนถล่ม |
| `chibaku.pullStrength` | 0.22 | แรงดึง |
| `chibaku.affectPlayers` | true | |
| `chibaku.maxEntities` | 48 | |
| `chibaku.maxAirborneTicks` | 60 (20–70) | คงต่ำกว่า 80 เพื่อไม่ให้โดนระบบ anti-fly-kick |
| `chibaku.interruptDistance` / `interruptDamage` | 6 / 3.0 | |
| `chibaku.maxSessions` | 4 | |

**`painorigin-client.toml`** (ฝั่งผู้เล่นแต่ละคน)

| ค่า | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `particles.enabled` | true | false = ไม่วาดพาร์ติเคิลของม็อดนี้ |
| `particles.reduced` | false | true = เก็บเพียง ~35% ของพาร์ติเคิลที่ไม่จำเป็น (เก็บเอฟเฟกต์หลักไว้) |
| `particles.additiveBlend` | true | ผสมสีแบบบวกให้คลื่น/แสงเรืองแสง (ปิดแล้วใช้ alpha ปกติ) |
| `particles.opacity` | 1.0 (0.1–1) | ความโปร่งใสรวม |
| `camera.shake` | true | เขย่ากล้องเมื่อมีระเบิด/ถล่มใกล้ |
| `camera.shakeStrength` | 1.0 (0–2) | |

### 8.2 ค่าที่อยู่ใน JSON ของพาวเวอร์ (ระยะ/แรง/คูลดาวน์/ค่าจักระ)

ระยะ แรงผลัก/ดึง คูลดาวน์ และค่าจักระของ **ชินระ เท็นเซ, บันโช เท็นอิน, ชาร์จป้องกัน, สนามแรงโน้มถ่วง** เป็นค่าใน JSON ที่ Apoli อ่าน
(ไม่ใช่ใน `.toml` เพราะ Apoli อ่านค่าเหล่านี้จากไฟล์พาวเวอร์) จึงมี 3 ทางปรับ:

1. **แก้ตรง ๆ** ที่ `data/painorigin/powers/*.json` (เช่น `shinra_tensei.json`: `cooldown`, `radius`, `add_velocity.z`, `change_resource.change`)
2. **สร้างใหม่ด้วยสคริปต์** (ค่าทั้งหมดอยู่ในตาราง `T` ที่หัว `tools/gen_data.py` และอัปเดตข้อความ/lang ให้สอดคล้อง):
   ```bash
   python3 tools/gen_data.py . --set=shinra_radius=14 --set=shinra_cooldown=60 --set=tenin_range=48
   ```
   ชื่อที่ใช้ได้: `chakra_max chakra_regen_interval chakra_regen_amount shinra_cost shinra_cooldown shinra_radius shinra_push_h shinra_push_v shinra_damage massive_cost massive_cooldown massive_charge massive_radius massive_push_h massive_push_v massive_damage tenin_cost tenin_cooldown tenin_range tenin_pull_h tenin_pull_v chibaku_cost chibaku_cooldown defense_max defense_regen_interval defense_cost defense_push_range field_radius field_interval field_pull frail_health gravity_modifier`
3. **Datapack ทับ โดยไม่ต้อง build ใหม่**: สั่ง `python3 tools/gen_data.py . --set=... --datapack=./my_tuning` ได้โฟลเดอร์เดนแพ็กที่มีเฉพาะไฟล์พาวเวอร์ → ใส่ใน `<โลก>/datapacks/` แล้ว `/reload`
   (ข้อความอธิบายในหน้าเลือก Origin มาจากไฟล์ภาษาในม็อด จึงยังโชว์ตัวเลขเริ่มต้นแม้ใช้ datapack)

> หมายเหตุ: ค่า "ระยะ/แรง/คูลดาวน์" ที่ผู้ใช้ขอปรับได้อยู่ใน JSON (ข้อ 8.2) ส่วน "จำนวนพาร์ติเคิล/ระยะเวลาเอฟเฟกต์/จำนวนบล็อกจิบาคุ/ขนาดสนามจิบาคุ" อยู่ใน `.toml` (ข้อ 8.1)
> ขนาดสนามแรงโน้มถ่วง**พาสซีฟ**ของรินเนกัน (6 บล็อก) อยู่ใน JSON (`field_radius`)

## 9. พาร์ติเคิล

6 ชนิด จาก PNG RGBA โปร่งใสจริงใน `assets/painorigin/textures/particle/` (สร้างด้วย `tools/gen_textures.py`; ขอบโปร่งใส 100% และสีของพิกเซลโปร่งใสถูก "bleed" ให้ไม่เกิดขอบขาว/ดำ — ตรวจด้วย `tools/check_textures.py` ผ่านทั้งหมด)

| ชนิด | ขนาดไฟล์ | ใช้ที่ไหน | การผสมสี |
|---|---|---|---|
| `shinra_tensei_wave` | 256² | วงคลื่นกระแทกแนวนอนของชินระ เท็นเซ | บวก (glow) |
| `shinra_tensei_burst` | 256² | แสงวาบหันหน้าเข้ากล้อง (และการถล่มจิบาคุ) | บวก (glow) |
| `bansho_tenin_aura` | 256² | ออร่าเส้นทางดึง/จุดที่โดนดึง | alpha |
| `chibaku_tensei_core` | 256² | แกนมืดของจิบาคุ (โตตามเฟส) | alpha |
| `chibaku_tensei_debris` | 128² (แผ่น 2×2 ก้อนหิน) | เศษหินจำลองบินเข้าแกน/กระเด็นตอนถล่ม | alpha |
| `rinnegan_energy` | 256² | เส้นพลังรินเนกัน ออร่ารอบตัว ประกายป้องกัน | alpha |

- ลงทะเบียนผ่าน Forge 1.20.1: `ModParticles` (DeferredRegister + `SimpleParticleType`), `ClientSetup` (`RegisterParticleProvidersEvent` → `registerSpriteSet`), คลาส `client/particle/*` (สืบจาก `TextureSheetParticle`), นิยาม `assets/painorigin/particles/*.json`
- สีเข้ม (แกน/ออร่า) ใช้ alpha blend ปกติเพราะการบวกสีทำให้มองไม่เห็นบนฉากสว่าง; สีสว่าง (คลื่น/แสงวาบ) ใช้บวก ส่ง `depthMask(false)` และปิด cull เพื่อกันขอบสี่เหลี่ยม
- เซิร์ฟเวอร์ส่งด้วย `force=true` เพื่อข้ามข้อจำกัดของ vanilla (ปิดด้วย `particles.overrideVanillaLimit=false`)
- **ปิด/ลดพาร์ติเคิล**: ฝั่งผู้เล่น `painorigin-client.toml` → `particles.enabled=false` หรือ `particles.reduced=true`; ฝั่งเซิร์ฟเวอร์ `particles.enabled=false` หรือลด `particles.countMultiplier`
- **ข้อจำกัดที่ทราบ**: วงคลื่นเป็นวงแนวนอนจึงมองจากระดับสายตาจะเห็นเป็นเส้นบาง; แสงวาบ/แกนจะจางลงเมื่อกล้องเข้าใกล้มาก (เพื่อไม่ให้บังจอ); ลำดับการวาดระหว่างพาร์ติเคิลสองประเภทการผสมสีไม่แน่นอนเมื่อซ้อนกัน; ไม่ได้ทดสอบร่วมกับ shader/Embeddium/OptiFine

## 10. เสียง

8 อีเวนต์เสียง (`painorigin:<ชื่อ>` ใน `sounds.json`) ผูกกับไฟล์ `.ogg` ใน `assets/painorigin/sounds/` พร้อมคำบรรยาย (subtitle) ไทย/อังกฤษ
จัดเป็น 6 กลุ่มตามเทคนิค (การจัดกลุ่มนี้เป็นของผู้เขียนโปรเจกต์ ปรับได้ใน `sounds.json`):

| กลุ่ม | อีเวนต์ | ไฟล์ |
|---|---|---|
| 1. ชาร์จ/ปล่อยชินระ เท็นเซ | `shinra_tensei.charge`, `shinra_tensei.release` | `charge.ogg`, `shinra_tensei.ogg` |
| 2. คลื่นกระแทก | `shinra_tensei.shockwave` | `shockwave.ogg` |
| 3. บันโช เท็นอิน | `bansho_tenin.pull` | `bansho_tenin.ogg` |
| 4. แกนจิบาคุ | `chibaku_tensei.core` | `chibaku_core.ogg` |
| 5. เศษหิน/ถล่มจิบาคุ | `chibaku_tensei.debris`, `chibaku_tensei.collapse` | `chibaku_debris.ogg`, `chibaku_collapse.ogg` |
| 6. การป้องกันสากล | `universal_defense.block` | `defense.ogg` |

- **ไฟล์เสียงที่แนบเป็น placeholder สังเคราะห์ (CC0)** สร้างด้วย `tools/gen_sounds.py` เองทั้งหมด — **ไม่มีเสียงจากอนิเมะ** และไม่ได้ดึงจากแหล่งที่มีลิขสิทธิ์
  ตรวจเชิงตัวเลข (ความยาว, peak, clipping, สเปกตรัม) ด้วย `tools/check_sounds.py` แต่ **ยังไม่มีคนฟังจริง** คุณภาพเสียงยังไม่ได้ประเมิน; เสียง 3 ไฟล์ (`shinra_tensei`, `chibaku_collapse`, `defense`) เริ่มด้วยแอมพลิจูดสูงทันทีเพราะเป็นเสียงกระแทก ซึ่งอาจได้ยินเป็นเสียงคลิกต้นเสียง
- **เปลี่ยนเป็นเสียงของคุณเอง**: วาง `.ogg` (mono, 44.1 kHz แนะนำ) ชื่อเดียวกันทับใน `assets/painorigin/sounds/` หรือทำ resource pack ที่มี `assets/painorigin/sounds.json` + ไฟล์ของคุณ ใช้เฉพาะเสียงที่คุณมีสิทธิ์ใช้

## 11. คำสั่งแอดมิน (`/painorigin ...`, ต้อง permission level ≥ 2)

| คำสั่ง | ทำอะไร |
|---|---|
| `/painorigin chibaku status` | จำนวนจิบาคุ เท็นเซ ที่ทำงานอยู่ |
| `/painorigin chibaku cancel` | ยกเลิกเทคนิคของผู้สั่ง |
| `/painorigin chibaku start` | เริ่มจิบาคุ (ปกติเรียกโดยพาวเวอร์ JSON — ใช้ตรงนี้ **ไม่หักจักระ/คูลดาวน์**) |
| `/painorigin test` | ทดสอบตัวเอง: พาร์ติเคิล 6 ชนิดและเสียง 8 อีเวนต์ลงทะเบียนแล้ว, damage type 2 ชนิดและ tag 2 ตัวโหลดแล้ว, ไฟล์พาวเวอร์/Origin ทั้งหมดอยู่ในข้อมูลที่โหลด — แจ้งจำนวนที่ผ่านหรือรายการที่ขาด |
| `/painorigin fx ...`, `/painorigin massive_blocks` | คำสั่งภายใน ที่พาวเวอร์เรียกเพื่อสร้างเอฟเฟกต์/ลบหลุม |

พาวเวอร์ JSON เรียกคำสั่งเหล่านี้ผ่าน Apoli `execute_command` ซึ่งใช้ permission level จากคอนฟิกฝั่งเซิร์ฟเวอร์ของ Apoli (`permission_level`, **ค่าเริ่มต้น 2** — ตรวจกับซอร์ส Apoli)
**ถ้าแอดมินลดค่านี้ต่ำกว่า 2 เทคนิคที่เรียกผ่านคำสั่งจะไม่ทำงาน** (เอฟเฟกต์พาร์ติเคิล/เสียงบางส่วน/จิบาคุ/หลุมของ Massive) ส่วนแรงผลัก/ดาเมจที่เป็น JSON ล้วนยังทำงาน
ผู้เล่นทั่วไปพิมพ์ `/painorigin` เองไม่ได้ (level 2 ขึ้นไป) ตั้งใจให้เป็นเช่นนั้น

## 12. รายงานการทดสอบ

### 12.1 สิ่งที่รันจริงแล้ว (ผลที่เกิดขึ้นจริง ณ ตอนแพ็ก)

| การตรวจ | ผล | หมายเหตุ |
|---|---|---|
| `tools/check_java.py` — `javac --release 17` ทั้ง 24 ไฟล์ | **REAL 0 / import ที่ไม่ได้ใช้ 0 → OK** | 848 ข้อผิดพลาดของ javac ถูกจัดประเภทหมด: 694 = คลาส Minecraft/Forge ที่หาไม่เจอ (คาดไว้ เพราะไม่มี jar), 137 = สมาชิกที่สืบจาก `Particle` (ตรวจชื่อกับรายการ), 17 = `@Override` ของ API ภายนอก; **ไม่ใช่การคอมไพล์จริง** ใช้จับ syntax, flow, ชื่อเมธอด/ตัวแปรของโค้ดเราเอง |
| `tools/verify_api.py` — เทียบชื่อ API กับซอร์สจริง 3,041 ไฟล์ (Forge 1.20.1, Botania, Iron's Spells, Apoli, Calio, Origins) | import/สมาชิก **ทุกตัวพบในซอร์สจริง**; เหลือให้ดูมือ 0 | พิสูจน์ได้แค่ว่า "ชื่อนี้มีอยู่จริงในโค้ด 1.20.1 อื่น" **ไม่พิสูจน์ชนิดอาร์กิวเมนต์** ชื่อที่ไม่อยู่ในคลังถูกตรวจมือและระบุแหล่งไว้ในสคริปต์ |
| `tools/validate_project.py` | **30 ผ่าน / 0 ไม่ผ่าน** | JSON parse ได้, ชนิดพาวเวอร์ทั้ง 34 ชนิดมีอยู่จริงใน Apoli/Origins, ไฟล์อ้างอิงครบ, lang ไทย/อังกฤษคีย์ตรงกัน, ModSounds = sounds.json = ไฟล์ .ogg, ModParticles = particles/*.json = PNG, placeholder ใน mods.toml ครบ; สคริปต์เองผ่านการทดสอบด้วยการฉีดข้อผิดพลาด 9 แบบแล้วจับได้ทั้งหมด |
| `tools/check_textures.py` | ALL OK | PNG ทั้ง 6 เป็น RGBA, ขอบโปร่งใส, ไม่มี halo ขาว/ดำ, แผ่นเศษหิน 4 ช่องมีขอบว่าง |
| `tools/check_sounds.py` | รันได้ ตัวเลขอยู่ในเกณฑ์ | peak 0.57–0.86, ไม่ clipping, ยาว 0.55–3.2 วิ (ไม่ใช่การฟัง) |
| สร้างทรัพยากรใหม่ด้วย `tools/gen_data.py` แล้ว `diff -r` กับที่แนบ | **เหมือนกันทุกไฟล์** | ยืนยันว่าสคริปต์กับไฟล์ที่แนบสอดคล้องกัน; ทดสอบ `--datapack` ได้โฟลเดอร์ + `pack.mcmeta` (pack_format 15) จริง; ทดสอบตัวอย่าง `--set=shinra_radius=14 ...` ในข้อ 8.2 แล้ว JSON และข้อความ lang เปลี่ยนตรงกัน และชื่อที่ไม่รู้จักถูกปฏิเสธ |
| สร้าง PNG/เสียงใหม่ด้วย `tools/gen_textures.py` / `tools/gen_sounds.py` เทียบกับที่แนบ | PNG ทั้ง 7 ไฟล์ **ตรงกันทุกไบต์**; เสียงทั้ง 8 ไฟล์ **ถอดรหัสแล้วตรงกันทุกตัวอย่าง** (ไบต์ของไฟล์ .ogg ต่างกันได้ เพราะ serial number ของคอนเทนเนอร์สุ่ม) | ยืนยันว่าสคริปต์ที่แนบคือที่มาของไฟล์จริง |

### 12.2 สิ่งที่ **ไม่ได้ทำ**
- ❌ `./gradlew build` (ต้องการเครือข่ายที่เครื่องสร้างเข้าไม่ถึง)
- ❌ คอมไพล์เทียบกับ Minecraft/Forge จริง → **ไม่รับประกันว่าคอมไพล์ผ่าน**
- ❌ เปิดเกม / เซิร์ฟเวอร์ dedicated / มัลติเพลเยอร์ / ทดสอบร่วมกับม็อดอื่น
- ❌ ตรวจโดยผู้รีวิวอิสระ (subagent ถูกตัดด้วย rate limit สามครั้ง ไม่มีรายงาน)
- ❌ ฟังเสียงจริง / ดูพาร์ติเคิลในเกมจริง (ตรวจ PNG แค่เชิงตัวเลขด้วยสคริปต์ ไม่ได้ดูการเรนเดอร์ในเกม)
- ❌ ตรวจว่า Apoli แปลงฟิลด์ของพาวเวอร์ทุกตัวถูกต้องขณะรันจริง (ตรวจแค่ชื่อชนิดพาวเวอร์และการอ้างอิงจากซอร์ส)

### 12.3 รายการทดสอบในเกม (แนะนำให้ทำตามลำดับ)
1. เกมเปิดได้ ไม่แครชตอนโหลด; ล็อกไม่มี error ของ `painorigin`
2. เลือก Origin เทวะมรรคได้ (หรือ `/origin set`); เห็นแถบจักระ; ตั้งปุ่มรองแล้ว
3. กดปุ่มหลัก: ผลักม็อบรอบตัว ไม่ทำลายบล็อก, เห็นวงคลื่น+แสงวาบ, ได้ยินเสียง, จักระลด 10, คูลดาวน์ ~5 วิ
4. Shift+ปุ่มหลัก: ชาร์จ 1.5 วิ แล้วผลักแรง, กล้องสั่น, ยืนยันว่า **ไม่มีบล็อกหาย**; เปิด `massive.blockDestruction` → หลุมไม่เกินค่าที่ตั้ง และไม่ลบ bedrock/บล็อกที่ผู้เล่นไม่มีสิทธิ์
5. ปุ่มรอง: ดึงม็อบที่มอง; ยืนหลังกำแพง → "ไม่มีเป้าหมายในสายตา" และไม่ดึง
6. Shift+ปุ่มรอง: ครบ 6 เฟส (ข้อความบน action bar เปลี่ยนตามเฟส), แกนปรากฏ, เศษหินบินเข้า, ถล่มแล้วจบ — ตรวจว่าโลก **ไม่เปลี่ยน** เมื่อ `realBlocks=false`
7. ยกเลิกจิบาคุด้วยการ: ตาย, ออกเกม, ข้ามมิติ (Nether), วิ่งห่างเกิน 6 บล็อก, โดนดาเมจแรง — ต้องหยุดทันทีและไม่มีสิ่งมีชีวิตค้างลอย
8. จิบาคุซ้อนหลายคน ไม่เกิน `maxSessions`; ม็อบใน `chibaku_immune` ไม่ถูกแตะ
9. การป้องกันสากล: ลูกธนู/ม็อบตี/ระเบิดถูกกัน 3 ครั้งแล้วหมดชาร์จ; ตกจากที่สูง/จมน้ำ/ไฟ **ไม่ถูกกัน**
10. สนามรินเนกัน: ไอเท็ม/XP ในรัศมี 6 บล็อกลอยเข้าหา
11. ปิดพาร์ติเคิล/ลดพาร์ติเคิล/ตั้ง `particles.opacity`, `camera.shake=false` ได้ผลจริง
12. เซิร์ฟเวอร์ dedicated (ไม่มีคลาสไคลเอนต์ถูกโหลดฝั่งเซิร์ฟเวอร์): ผู้เล่นเข้าร่วมแล้วใช้ทุกเทคนิคได้ ไม่มีแครช
13. ตรวจที่ Apoli `permission_level` = 2 ว่าพาวเวอร์เรียก `/painorigin` ได้

## 13. ข้อจำกัดที่ทราบ (สรุป)

- ยังไม่เคยคอมไพล์/ทดสอบในเกม (ดูข้อ 12.2) — คาดว่าอาจต้องแก้ชื่อ/ซิกเนเจอร์ API เล็กน้อยหลัง build ครั้งแรก
- จิบาคุ เท็นเซ: เศษหินเป็นภาพจำลอง; บล็อกจริงถูกลบได้เฉพาะโหมดทดลอง `realBlocks` และเฉพาะตอนถล่มสุดท้าย; ไม่ได้เช็ก spawn protection ของ vanilla โดยตรง (เช็กผ่าน `BreakEvent`, `mayBuild`, ขอบโลก) — เซิร์ฟเวอร์ที่ป้องกันด้วยม็อดอื่นต้องให้ม็อดนั้นฟัง `BreakEvent`
- พาร์ติเคิลวงคลื่นเป็นแนวนอน (เห็นเป็นเส้นบางจากระดับสายตา); ใช้ easing แบบเดียวกันทั้งขาเข้า/ขาออกของเศษหิน
- เสียงเป็น placeholder สังเคราะห์ CC0 ยังไม่ผ่านการฟังจริง
- ตัวเลขใน JSON ต้อง `/reload` (หรือเริ่มเกมใหม่) จึงมีผล; ข้อความบรรยาย Origin ไม่เปลี่ยนตามตัวเลขที่ปรับ
- การเปลี่ยนตัวเลข "ชินระ/บันโช/ป้องกัน" ไม่มีทางทำใน `.toml` (ข้อ 8.2)
- ถ้า Apoli `permission_level` ต่ำกว่า 2 ส่วนหนึ่งของเทคนิคจะไม่ทำงาน (ข้อ 11)
- จักระถูกหักแม้ปิดจิบาคุในคอนฟิก
- ไม่รองรับ Fabric/Quilt และไม่ใช่ Minecraft เวอร์ชันอื่น

## 14. โครงสร้างโปรเจกต์

```
PainOrigin/
├─ build.gradle  settings.gradle  gradle.properties  gradlew(.bat)  gradle/wrapper/
├─ .github/workflows/build.yml          (CI สำหรับ build ด้วย Java 17 — ไม่เคยรันจริง)
├─ README.md  LICENSE
├─ tools/                               (สคริปต์สร้าง/ตรวจ — ไม่ถูกรวมใน jar)
│   ├─ gen_data.py  gen_textures.py  gen_sounds.py          สร้างทรัพยากร
│   │    python3 tools/gen_data.py .                                   (JSON/lang/sounds.json/particles/pack.mcmeta)
│   │    python3 tools/gen_textures.py <dir อนุภาค> <dir gui>          (ต้องมี numpy, scipy, Pillow)
│   │    python3 tools/gen_sounds.py <dir เสียง> <dir ชั่วคราว>        (ต้องมี numpy, scipy, ffmpeg+libvorbis)
│   ├─ check_java.py  verify_api.py  validate_project.py    ตรวจแบบสแตติก
│   ├─ check_textures.py  check_sounds.py
│   └─ gen_apoli_types.py  apoli_types.json                 รายชื่อชนิดพาวเวอร์ของ Apoli/Origins ที่ใช้ตรวจ
└─ src/main/
    ├─ java/com/painorigin/
    │   ├─ PainOrigin  CommonEvents  PainCommands  PainConfig  PainClientConfig
    │   ├─ ModParticles  ModSounds  Fx  FxStyle
    │   ├─ ChibakuManager  BlockSafety  MassiveBlocks
    │   └─ client/  ClientSetup  ClientEvents  CameraShake
    │        └─ particle/  PainParticle  PainRenderTypes  ParticleFilter
    │             ShinraWaveParticle  ShinraBurstParticle  BanshoAuraParticle
    │             ChibakuCoreParticle  ChibakuDebrisParticle  RinneganEnergyParticle
    └─ resources/
        ├─ META-INF/mods.toml   pack.mcmeta
        ├─ assets/painorigin/  lang/{en_us,th_th}.json  sounds.json  sounds/*.ogg
        │                      particles/*.json  textures/particle/*.png  textures/gui/resource_bar.png
        └─ data/
            ├─ origins/origin_layers/origin.json
            ├─ painorigin/  origins/deva_path.json  powers/*.json (17)
            │               damage_type/{shinra_tensei,chibaku_tensei}.json
            │               tags/blocks/chibaku_protected.json  tags/entity_types/chibaku_immune.json
            └─ minecraft/tags/damage_type/bypasses_armor.json
```

## 15. สัญญาอนุญาตและเครดิต

- โค้ด: **MIT** (ดู `LICENSE`)
- พาร์ติเคิล PNG และเสียง `.ogg`: สร้างโดยสคริปต์ในโปรเจกต์นี้ เผยแพร่เป็น **CC0** — ไม่มีสินทรัพย์จากอนิเมะ/มังงะ
- "Naruto", "Pain/Nagato", ชื่อเทคนิคต่าง ๆ เป็นของ Masashi Kishimoto / Shueisha / Pierrot ฯลฯ โปรเจกต์นี้เป็นงานแฟนเมดไม่เป็นทางการ ไม่ได้รับการรับรอง และไม่ได้ใช้ตัวละคร ภาพ หรือเสียงต้นฉบับ
- Origins, Apoli, Calio เป็นของผู้พัฒนาแต่ละราย (ไม่ได้รวมมาในแพ็กเกจนี้)
