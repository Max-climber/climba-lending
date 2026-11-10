# CLIMBA Intro — промпты Magnific

Кредиты тратятся только по явному «трать N». Сначала 3D-модель панды, видео — после того как модель ок.

## 0. 3D-модель панды (делаем первой, отдельно)

Не видео. Не сцена. Не буквы. Только персонаж.

### Figma не нужна. Нужны чистые PNG

Magnific не читает Figma. Ему нужны картинки или текст. Живой доступ к файлу Фигмы ничего не даёт генератору и часто тянет рамки, кнопки, чужие аватарки.

Что экспортировать из Фигмы **самому** (PNG, без фона UI, по одному персонажу на кадр):

| Файл | Зачем |
|------|--------|
| `refs/mascot_guidebook.png` | канон: голова, уши, пятна, пропорции |
| `refs/expressions/sheet_body_moods.png` | мимика тела: усталость, победа, злость, ранение, грусть |
| `refs/expressions/sheet_fight_cry.png` | брови / плач — как гнутся пятна и рот |
| `refs/expressions/mascot_chalkbag.png` | мешок с магнезией, открытый рот |
| turnaround, если есть: фронт / 3/4 / бок / спина | объём, не стикер |

Виджеты (`widgets_moods.png`) — только как каталог эмоций, в 3D не кормить: там интерфейс.

### Все настроения — в чертёж форм, не в одну сетку

Одна GLB = **одно тело + одно rest-лицо**. Если в промпт запихнуть «злая, плачет, радуется» сразу, модель слепит гибрид: два рта, сросшиеся брови, лишние руки.

Настроения используем так:

1. **Сейчас (700 кр.)** — A-pose, нейтральное rest-лицо. В промпте перечислены **инварианты**, которые видны во всех позах: шар головы, почечные пятна, нос, короткий корпус.
2. **Потом (после утверждения GLB)** — лист эмоций тем же персонажем: determined, proud, straining, dizzy, laughing, angry, sad. Это 2D/рендеры, не вторая скульптура.

Интро использует в основном: determined → straining → dizzy → laughing.

| Инструмент | Модель | Поза | Кредиты | Зачем |
|------------|--------|------|---------|--------|
| `models3d_text_generate` | Meshy 7.1 | A-pose | **700** | первая модель, чистая топология |
| `models3d_generate` | Tripo H3.1 / Meshy 7.1 | из картинки | **1160** | только если сначала сделаем 3D-рендер маскота, не из стикера |

### Промпт (вставлять целиком)

```
A single 3D mascot character of the Climba brand panda cub, full body, standing in a clean
A-pose, feet planted on an invisible ground, arms slightly out from the torso, palms open,
soft rounded mitten paws, no fingers sculpted separately. One character only. Rest face:
neutral, tiny friendly closed-mouth smile, eyes looking forward. Do not sculpt extra
expressions onto this mesh. Stylized Pixar / premium animated-feature sculpture, not a toy,
not a plush, not a sticker, not a relief, not a flat cutout.

Construction bible — these forms stay identical in every mood of the 2D sheets, so sculpt
them as simple deformable volumes:

HEAD is a huge smooth sphere, about 40 percent of total height, pale off-white #F4F3F6.
Two round black ears sit on top of the sphere, slightly tilted outward, like two small balls
half-sunk into the skull, inner ear a touch lighter. No forehead wrinkles. No neck: the head
sits directly on the belly sphere.

EYE PATCHES are two large soft black kidney / bean shapes, one around each eye. They never
become a bandit mask. They stay the same silhouette when the character is happy, angry or
sad — only the eyes and brows move inside them. Inner corners point toward the small nose
but do not merge into one patch.

EYES are oversized glossy black cartoon discs inside the patches, with two white highlights
each (a big one and a tiny one). On the rest face they are round, open, looking forward,
slightly curious. Leave the lids simple so they can later squint (anger), look up (dreamy),
or squeeze shut (laugh, cry). No eyelashes. No human eyelids.

BROWS are not separate meshes: a slight thickening at the top inner edge of each black
patch is enough. Do not sculpt angry V-brows on the rest face.

MUZZLE is a very short soft bump on the lower front of the head. Small rounded black nose
centered low, like a tiny bean. Mouth is a simple closed curved line, tiny smile, no teeth,
no tongue, no open jaw. Cheeks stay round and chubby so they can puff for a laugh or droop
for sadness later.

BODY is a second white sphere, the belly, sitting low. Short black sausage arms attached
to the upper sides of the belly. Short black plantigrade legs under the belly, knock-kneed,
top-heavy like a toddler cub. Soft mitten paws, no claws, no pads. Silhouette = stack of
soft spheres. Cute, weighty, huggable.

A small closed chalk bag on a simple belt at the right hip, beige / dark grey fabric, brand
prop, not a backpack, not a sack of cards. One optional tiny chalk puff.

Surface: short dense velvety fur, not long shag, not photoreal bear, not rubber, not vinyl.
Clean color blocks white #F4F3F6 and black #2B2430. No outline, no cel-shading, no sticker
white border.

Lighting on the texture: even studio lighting, no baked hard shadows, no HDRI streaks.
Watertight mesh, closed mouth, no holes, no extra limbs. Centered, origin at the feet,
facing camera, A-pose.
```

### Negative

```
flat, 2D, sticker, outline, white border, relief, bas-relief, coin, paper cutout,
photoreal bear, scary, teeth, tongue, claws, long fur, dirty fur, human, clothes,
hat, glasses, headband, swords, notepad, trophy, duffel bag, band-aid, backpack,
extra limbs, extra ears, extra faces, multiple characters, angry brows on rest face,
crying, tears, open laughing mouth, squinting, sitting, jumping, climbing, T-pose
with stretched arms, letters, logo, UI, widgets, background objects, ground plane,
pedestal, text, watermark
```

### Параметры вызова

```
provider: meshy
aiModel: meshy-7.1
poseMode: a-pose
texture: true
prompt: <блок выше>
negativePrompt: <блок выше>
```

После модели: смотрим GLB. Если шар головы, пятна и живот совпадают с гайдбуком — ок.
Мимику (злость, плач, смех) не правим новой скульптурой: делаем лист эмоций тем же персонажем.

### Следующий шаг после GLB — лист эмоций (не запускать сейчас)

Референсы: утверждённая 3D-панда + `refs/expressions/*.png`.

```
Same 3D Climba panda as the character reference, identical proportions and face construction.
Character sheet on a plain light grey background: rest A-pose, then busts only —
determined looking up, proud, straining while hanging, dizzy, laughing with eyes squeezed
and belly shake, angry frown with eyes inside the same kidney patches, sad droop.
Do not change the ear, patch or belly shapes. Only brows, eyelids and mouth deform.
```

---

## 1. Как устроено видео (после модели)

Канон персонажа — **`master_c`**. Не A/B/D.

- Таймлайн **12 с** = 4 куска по 3 с (24 fps, 288 кадров). Kling 3.0 = ровно 3 с.
- Стык: последний кадр куска N = первый кадр куска N+1.
- Ключевые кадры: `0001, 0072, 0144, 0216, 0288`.
- `plate_####.png` — буквы без панды; `guide_####.png` — позиция.
- **Точка над i никогда не двигается и не падает.**
- Буквы всегда **позади** панды. Она катится по полу, не по буквам.
- Ракурс камеры **один** на весь ролик (тот же наклон). Сначала близко, панда почти в центре, камера едет за ней влево. С ~9 с плавный отъезд, чтобы было видно всё слово. Никакого другого угла, никакого крана вверх.

### Сюжет

Панда **кувыркается вперёд** справа налево **в профиль**: смотрит влево, бок к камере. Кувырок через голову, как живой детёныш — круглый, медленный, squash в пол, лапы болтаются. Не паркур, не сальто гимнаста. Упирается в «i», пытается **перелезть** через букву: хватается за точку, задние лапы болтаются в воздухе. Переваливается, срывается максимально нелепо, падает, садится, поворачивается к камере и смеётся.

### Затемнение — в промпте последнего куска

Kling гасит картинку сам. В S4 слово целиком читается, панда уже сидит и смеётся, и только **после этого** (с ~11.2 с) сцена тускнеет в чёрный. Не cut, не freeze.

Срезы на движении:

| Кадр | Что в кадре |
|------|-------------|
| 0001 | в профиль справа от «a», смотрит влево, буквы позади |
| 0072 | кувырок в профиль, всё ещё катится, буква «b» позади, без остановки |
| 0144 | уперлась в «i», смотрит вверх на столбик, в профиль |
| 0216 | висит на точке, задние лапы болтаются, пытается перелезть |
| 0288 | сидит слева от «i», лицом в камеру, смеётся, слово целиком |

## 2. Общие блоки для видео

**CHARACTER** (lock to `master_c`):
```
chubby round panda mascot "Climba" identical to the master_c still: huge spherical white head,
oversized glossy cartoon eyes with dark charcoal irises, black pupils and two white highlights,
soft black kidney eye patches that never become a mask, small black nose, tiny closed-mouth
smile, round black ears, short black sausage arms and legs, round white belly, stubby cub
proportions. Moves like a real giant-panda cub: plantigrade, top-heavy, slow, clumsy, she
rolls as a round ball. Soft even studio lighting, she is NOT a lamp, no light beams,
no god rays, no glowing halo. Black patches stay dark. Never dim, never a silhouette.
```

**STYLE**:
```
premium stylized 3D animated feature film look, soft global illumination, even studio light,
soft velvety fur, no emission, no light rays from the character, clean simple shapes,
appealing cartoon proportions, weighty panda body mechanics, squash-and-stretch on each
roll contact, never snappy parkour
```

**SCENE**:
```
seamless soft periwinkle-blue studio cyclorama, no horizon line, soft diffuse cool light, soft contact
shadows, big matte near-black 3D lowercase letters "climba" standing on the floor with wide gaps
between them
```

**NEGATIVE**:
```
changing letters, extra letters, melting or morphing letters, text distortion, the i-dot moving or
falling or detaching, extra limbs, realistic bear, scary face, fur clumps, parkour, snow, flour, foam,
backflip, gymnast tumbling, jumps, hopping along letter tops, climbing a, climbing b, climbing m,
climbing l, climbing c, freeze, idle, flicker, jitter, sudden cuts, camera shake, camera angle change,
crane up, new viewpoint, blur, watermark, cut to black, smash cut, dim panda, dark silhouette,
underexposed character, small bead eyes, brown irises, changing the face away from master_c,
light rays, god rays, spotlight beams, glowing halo, character as a lamp, volumetric light
```

## 3. Ключевые кадры (после 3D-модели)

Референсы: `plate_####.png`, `guide_####.png`, **только `master_c`**.

```
Use the first image as the exact background: keep the letters, camera, framing and colors unchanged.
Place the panda from master_c exactly where the placeholder is in the second image, same size.
The panda is IN FRONT of the letters, closer to camera. Identical face to master_c: oversized
cartoon eyes with dark charcoal irises. CHARACTER, STYLE. Pose: <POSE>
```

| Кадр | `<POSE>` |
|------|----------|
| 0001 | standing in profile to the right of "a", looking left (face points left, side to camera), letters behind her, about to forward-roll |
| 0072 | mid forward-roll in profile looking left, still moving past "b", NOT sitting, NOT stopping |
| 0144 | sitting at the "i" in profile, looking up the stem, about to climb over it |
| 0216 | hanging from the i-dot by both front paws, trying to haul over the letter, hind legs dangling and kicking, the dot does not move |
| 0288 | sitting on the floor to the left of "i", facing the camera, laughing, whole word visible |

## 4. Видео (Kling 3.0, 3 с, start + end frame, character = 3D-панда)

Цена: 210 кр. (720p) / 270 кр. (1080p) за кусок. Не запускать, пока 3D-модель не утверждена.

Промпт = только движение, камера и затемнение. Буквы держит кадр. **Точка над i неподвижна.**
Ракурс не менять. Панда = `master_c`.

### 9:16 и 16:9 — одни промпты

**S1 · 0–3 с · 0001 → 0072**

```
Close shot, panda almost centered, IN PROFILE looking left: her face points left, her
side toward camera. She stands on the floor to the right of "a"; the letters stand behind
her. Same camera angle the whole shot. She tucks her head and rolls in a continuous series
of clumsy FORWARD somersaults to the left, never stopping, never sitting, never pausing
at "b": head over belly, limbs flop, squash on each contact, not a gymnast, not a
sideways cartwheel, not facing the camera. Camera trucks left with her, keeping her near
the center. End still rolling, in profile looking left.
```

**S2 · 3–6 с · 0072 → 0144**

```
Same camera angle, still in profile looking left, still rolling — no pause. Continuous
forward somersaults leftward across the floor, round and heavy, flopping paws. She does
not climb a, b or m. She reaches the "i" and immediately starts climbing it, no sit, no
idle. Camera trucks left with her, no angle change.
```

**S3 · 6–9 с · 0144 → 0216**

```
Same camera angle, still close, still in profile looking left. She tries to climb OVER the
letter "i": crawls up the stem belly-close, grabs the underside of the i-dot with both front
paws, and her hind legs dangle and kick helplessly as she tries to haul her round belly over
the letter, like a cub stuck on a branch. Two slip-backs. The i-dot never moves. Camera
keeps her centered. No new angle.
```

**S4 · 9–12 с · 0216 → 0288**

```
Same camera angle. She finally hauls her belly over the still i-dot, then loses it and falls
in the clumsiest panda somersault: over-rotates, limbs flop, and she HITS THE FLOOR on her
back, belly up, dazed. WHILE she is falling the camera dollies back until the entire word
"climba" is readable, then HOLDS. Do not change the camera angle or tilt. Only AFTER the
wide shot is held does she sit up, turn to FACE THE CAMERA, and burst out laughing, belly
shaking, eyes squeezed, tiny happy grin. Keep holding the readable word.

CRITICAL ENDING: after the word has been readable long enough to read "climba", during the
last 0.8 seconds, while she is still smiling and the whole word is readable, the entire
image smoothly dims and fades to full black. Continuous fade, no cut, no freeze, no flash.
The laugh/smile continues through the fade. Hold black at the very last frames.
```

## 5. Монтаж (24 fps)

1. S1…S4 встык с шагом 3 с. На стыках убрать 1 дублирующийся кадр.
2. Если Kling не погасил S4 — в монтаже fade to black **11.2–12.0 с**.
3. Логотип целиком читается ~10.2–11.2 с, затем тускнеет.
4. Экспорт: 9:16 1080×1920 и 16:9 1920×1080, H.264, 24 fps.

### Звук

| Время | Звук |
|-------|------|
| 0.0–0.4 | тихий вдох, замах |
| 0.4–3.0 | кувырки вперёд, «бух» на каждом контакте |
| 3.0–3.4 | головокружение, пых |
| 3.4–5.8 | ещё кувырки, «бух-бух» |
| 5.8–6.2 | стоп у «i», взгляд вверх |
| 6.2–7.8 | царапанье вверх по столбику |
| 7.8–8.1 | «чпок» хват за точку |
| 8.1–9.0 | задние лапы молотят, срывы |
| 9.0–9.4 | перевал через точку |
| 9.4–10.1 | нелепый срыв, «бум» — падает на спину |
| 10.1–10.5 | лежит, садится, поворот к камере |
| 10.5–11.5 | смех → вместе с картинкой затухает |
| 11.5–12.0 | чёрный, тишина |

## 6. Бюджет (видео не считать, пока нет модели)

| Что | Кредиты |
|-----|---------|
| 3D-панда, Meshy 7.1 A-pose | **700** |
| запас на одну перегенерацию модели | 700 |
| ключи + 4 клипа 1080p 9:16 | позже, после модели |
