"""
make_tutorial_figures.py — figures for the step-by-step tutorial (WWTP_annotation_tutorial_v1.docx).

Outputs annotation/manual/figures_tutorial/*.png:
  G1..G9  "이렇게 생겼으면 이 이름" galleries: real crops from pilot / practice images with the box the
          annotator should draw, class name, Korean name and a one-line hint
  S1..S3  pilot image 1 in three states (units only → + connection elements → + edges)
  PR1..PR5 answer keys for the five practice images (boxes + class list)
Screenshots of Label Studio (U*.png) are captured separately (see build_tutorial.py header).

Coordinates are in original image pixels and were picked by eye; they are illustration, not ground truth.
"""
from __future__ import annotations

import glob
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
PIL_DIR = ROOT / "data" / "pilot"
OUT = Path(__file__).resolve().parent / "figures_tutorial"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "C:/Windows/Fonts/malgun.ttf"
FONTB = "C:/Windows/Fonts/malgunbd.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"
MONOB = "C:/Windows/Fonts/consolab.ttf"

C = {"unit": "#0F7B6C", "zone": "#2C5F8A", "generic": "#444444", "io": "#B8701E", "junction": "#C0392B",
     "instrument": "#7A3E9D", "no": "#9E9E9E", "parent": "#1B4F72"}


def font(size, bold=False, mono=False):
    return ImageFont.truetype((MONOB if bold else MONO) if mono else (FONTB if bold else FONT), size)


_IMG: dict[str, Image.Image] = {}


def img(key: str) -> Image.Image:
    """key = 'p02' (pilot number) or 'x1' (practice number)."""
    if key not in _IMG:
        if key.startswith("x"):
            pat = str(PIL_DIR / "practice" / "images" / f"practice_{int(key[1:]):02d}__*")
        else:
            pat = str(PIL_DIR / "images" / f"pilot_{int(key[1:]):02d}__*")
        _IMG[key] = Image.open(glob.glob(pat)[0]).convert("RGB")
    return _IMG[key]


# ----------------------------------------------------------------------------- gallery tiles
def tile(key, box, color, extra_boxes=(), height=190, max_w=330, pad_frac=0.35, pad_min=26):
    im = img(key)
    x0, y0, x1, y1 = box
    px, py = max(pad_min, int((x1 - x0) * pad_frac)), max(pad_min, int((y1 - y0) * pad_frac))
    cx0, cy0 = max(0, x0 - px), max(0, y0 - py)
    cx1, cy1 = min(im.width, x1 + px), min(im.height, y1 + py)
    crop = im.crop((cx0, cy0, cx1, cy1))
    s = height / crop.height
    if crop.width * s > max_w:
        s = max_w / crop.width
    crop = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    for (bx, bc) in [(box, color)] + list(extra_boxes):
        r = [(bx[0] - cx0) * s, (bx[1] - cy0) * s, (bx[2] - cx0) * s, (bx[3] - cy0) * s]
        d.rectangle(r, outline=bc, width=3)
    return crop


def gallery(name, title, items, cols=4, cell_w=335, tile_h=190, text_h=78, subtitle=""):
    """items: (key, box, color, line1, line2, line3, extra_boxes)"""
    rows = (len(items) + cols - 1) // cols
    top = 50 if subtitle else 44
    W, H = cols * cell_w + 20, top + rows * (tile_h + text_h + 14) + 10
    canvas = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(canvas)
    d.text((14, 10), title, fill="#1B2A33", font=font(20, True))
    if subtitle:
        d.text((14 + d.textlength(title, font=font(20, True)) + 14, 15), subtitle, fill="#5C6B75", font=font(13))
    for i, it in enumerate(items):
        key, box, color, l1, l2, l3 = it[:6]
        extra = it[6] if len(it) > 6 else ()
        r, c = divmod(i, cols)
        ox, oy = 10 + c * cell_w, top + r * (tile_h + text_h + 14)
        t = tile(key, box, color, extra, height=tile_h, max_w=cell_w - 16)
        d.rectangle([ox, oy, ox + cell_w - 10, oy + tile_h + text_h + 4], outline="#E3E6E8", width=1)
        canvas.paste(t, (ox + (cell_w - 10 - t.width) // 2, oy + (tile_h - t.height) // 2 + 2))
        d.rectangle([ox + 8, oy + tile_h + 8, ox + 18, oy + tile_h + 18], fill=color)
        d.text((ox + 24, oy + tile_h + 6), l1, fill=color, font=font(13, True, l1.isascii()))
        d.text((ox + 8, oy + tile_h + 28), l2, fill="#1B2A33", font=font(13, True))
        d.text((ox + 8, oy + tile_h + 50), l3, fill="#5C6B75", font=font(11.5))
    canvas.save(OUT / f"{name}.png")
    print("saved", name, canvas.size)


U, Z, G, IO, J, IN, NO, P = C["unit"], C["zone"], C["generic"], C["io"], C["junction"], C["instrument"], C["no"], C["parent"]


def galleries():
    gallery("G1_preliminary", "전처리 — 스크린·침사지·유량조정조·펌프장", [
        ("p34", (133, 112, 167, 176), U, "screen", "스크린 (기호형)", "세로 막대·격자 기호. 굵은 선 하나면 스크린"),
        ("p17", (390, 65, 437, 112), U, "screen", "스크린 (기계식, 그림형)", "빗살 상자. Manual·Mechanical 둘 다 screen"),
        ("p10", (120, 88, 260, 338), U, "screen", "스크린 (글자 상자형)", "글자로 알았으니 visual_form=box"),
        ("p02", (72, 148, 98, 182), U, "screen", "스크린 (작은 기호 + 위 글자)", "기호에 박스, 위 글자는 치지 않음(쉬운 버전)"),
        ("p34", (205, 95, 302, 186), U, "grit_chamber", "침사지 (Grit Removal)", "모래 빼는 수로·탱크"),
        ("p02", (115, 108, 168, 195), U, "grit_chamber", "침사지 (Scum & Grit Removal)", "거품·모래 제거도 침사지"),
        ("p16", (125, 55, 195, 120), U, "grit_chamber", "모래·유지 분리조", "Sand, fat and oil separator → 침사지 + 메모"),
        ("x4", (100, 120, 235, 192), U, "pump_station", "침사지 및 유입펌프장 (한 덩어리)", "바깥 pump_station, 안쪽 침사지는 자식 grit_chamber"),
        ("p02", (470, 124, 520, 176), U, "equalization_tank", "유량조정조 (PCE Equalization)", "유량을 고르게 하는 탱크"),
        ("p23", (700, 470, 825, 530), U, "equalization_tank", "EQ (글자 상자)", "EQ = equalization. visual_form=box"),
        ("p53", (668, 365, 880, 475), U, "pump_station", "펌프장 (글자 상자)", "pumping station → pump_station"),
        ("x2", (1340, 1897, 1686, 2139), U, "pump_station", "Sewer Lift Station (특허)", "lift station = 펌프장"),
    ])

    gallery("G2_primary_secondary", "1차·2차 처리 — 침전지·생물반응 구역", [
        ("p34", (300, 118, 452, 166), U, "primary_clarifier", "1차 침전지 (그림형)", "생물반응조 앞, 슬러지가 농축·소화로"),
        ("x4", (257, 70, 330, 122), U, "primary_clarifier", "최초침전지", "최초 = 1차"),
        ("p02", (364, 40, 448, 212), U, "primary_clarifier", "1차 침전지 (기호형)", "V자 바닥 사다리꼴"),
        ("p17", (498, 215, 582, 296), U, "primary_clarifier", "Primary sedimentation (원)", "원으로 그려도 침전지"),
        ("p48", (242, 125, 460, 250), Z, "aerobic_zone", "Aeration Tank (상자)", "포기조. 구역이면 is_zone"),
        ("p17", (245, 232, 442, 292), Z, "aerobic_zone", "Aeration tank (교반기 그림)", "산기·교반 기호가 안에 있어도 탱크 하나로"),
        ("p02", (650, 112, 700, 218), Z, "aerobic_zone", "AER CSTR (칸마다 하나)", "나란한 칸 5개면 박스 5개"),
        ("p34", (498, 280, 582, 322), Z, "aerobic_zone", "Solids Contact (접촉 포기조)", "공기 들어가는 생물 탱크"),
        ("p02", (592, 112, 634, 218), Z, "anaerobic_zone", "ANA CSTR (혐기조)", "유입을 가장 먼저 받는 교반 칸"),
        ("p44", (270, 100, 330, 158), Z, "anoxic_zone", "Anoxic (격자무늬 칸)", "교반만, 질산염 반송을 받음"),
        ("p23", (700, 405, 825, 470), Z, "anaerobic_zone", "Anaerobic Zone (글자 상자)", "글자로 알았으니 box"),
        ("x4", (472, 70, 548, 122), U, "secondary_clarifier", "최종침전지", "최종 = 2차. 생물반응조 뒤"),
        ("p34", (328, 280, 418, 322), U, "secondary_clarifier", "Clarifiers (12) — 하나만", "'(12)'는 글자뿐이니 박스 1개"),
        ("p10", (860, 88, 1090, 338), U, "secondary_clarifier", "역삼각형 기호", "V 기호 = 침전지, visual_form=symbol"),
        ("x5", (225, 25, 305, 105), U, "secondary_clarifier", "Biomass separation (원뿔)", "생물 반응기 뒤 원뿔 = 2차 침전지"),
        ("x4", (588, 118, 692, 198), U, "secondary_clarifier", "응집침전지", "label_text에 '응집침전지'. 약품은 선으로"),
        ("p44", (475, 75, 570, 160), U, "mbr_unit", "MBR Tank", "혼합액을 받는 막 탱크"),
        ("x2", (632, 372, 1190, 639), U, "mbr_unit", "Membrane Tank (특허)", "Return flow로 슬러지를 돌려보냄"),
        ("p34", (545, 38, 672, 162), U, "biofilm_reactor/trickling_filter", "살수여상 (Trickling Filters)", "슬래시 뒤 세부형까지 고른다"),
        ("p16", (210, 55, 302, 122), U, "biofilm_reactor/mbbr_ifas", "MBBR (담체 알갱이)", "담체 떠다니는 탱크"),
        ("x5", (12, 10, 75, 355), U, "biofilm_reactor/fluidized_expanded_bed", "Fluidized bed reactor (탑)", "점 무늬 기둥"),
        ("p53", (668, 185, 880, 320), U, "biofilm_reactor/trickling_filter", "Trickling filters (글자 상자)", "box여도 세부형까지"),
        ("p44", (140, 290, 215, 445), U, "anaerobic_wastewater_reactor/anaerobic_mbr", "Anaerobic MBR (폐수 혐기 반응기)", "폐수가 들어가면 digester 아님"),
        ("x4", (190, 350, 272, 422), U, "sidestream_reactor", "반류수처리시설", "반류수만 받는 생물 반응기"),
    ])

    gallery("G3_tertiary", "3차 처리·소독·물리화학", [
        ("x4", (700, 130, 776, 188), U, "filtration_unit", "여과시설", "모래·디스크·섬유 여과"),
        ("x1", (270, 330, 330, 380), U, "filtration_unit", "Kelly Filter", "이름에 Filter → 여과"),
        ("p44", (275, 385, 345, 418), U, "membrane_unit", "PVDF MF Membrane", "처리수를 받는 막 = membrane_unit"),
        ("x1", (470, 250, 560, 300), U, "membrane_unit", "RO", "역삼투 = 막"),
        ("x4", (782, 130, 852, 182), U, "disinfection_unit", "소독시설", "UV·염소·오존"),
        ("p34", (160, 295, 278, 336), U, "disinfection_unit", "Disinfection (접촉조)", "긴 직사각형 수로"),
        ("p10", (1095, 88, 1340, 338), U, "disinfection_unit", "Sodium Hypochlorite Disinfection", "글자 상자. box"),
        ("p17", (165, 425, 287, 487), U, "disinfection_unit", "Disinfection (칸막이 수로)", ""),
        ("p16", (330, 55, 440, 125), U, "chemical_treatment_unit", "Coagulation & flocculation", "응집·교반 탱크가 그려짐"),
        ("x1", (258, 195, 305, 245), U, "chemical_treatment_unit", "Neutralization", "중화조"),
        ("p16", (468, 62, 540, 122), U, "flotation_unit", "DAF (용존공기부상)", "기포·부상 = flotation"),
        ("p02", (258, 240, 300, 262), G, "unknown_equipment", "Chiller (목록에 없음)", "label_text='Chiller', l1_hint=preliminary"),
    ])

    gallery("G4_sludge", "슬러지 처리", [
        ("x4", (612, 255, 684, 300), U, "thickener", "원심농축기", "농축 = thickener"),
        ("x4", (312, 388, 392, 432), U, "thickener", "드럼형농축기", "소화조 앞 드럼·벨트는 농축"),
        ("p17", (240, 632, 352, 702), U, "thickener", "Sludge concentrator", "concentrator = 농축"),
        ("x4", (415, 375, 482, 447), U, "digester", "소화조", "달걀·돔형 탱크, 슬러지 유입"),
        ("p17", (395, 632, 472, 707), U, "digester", "Anaerobic digester", ""),
        ("x4", (536, 385, 622, 447), U, "dewatering_unit", "탈수시설", "산물이 케이크"),
        ("p16", (540, 150, 652, 195), U, "dewatering_unit", "Centrifuge (탈수)", "슬러지 라인의 원심분리기"),
        ("p50", (130, 245, 330, 420), U, "drying_incineration_unit", "Fluidised bed incinerator", "소각로"),
        ("x3", (245, 555, 565, 1320), U, "drying_incineration_unit", "Multiple Hearth Furnace", "다단 소각로"),
        ("p44", (605, 98, 730, 160), U, "storage_tank", "Holding Tank", "모아 두는 탱크"),
        ("p17", (120, 632, 205, 707), U, "storage_tank", "Sludge mixing", "혼합·저류"),
        ("p50", (385, 165, 475, 320), G, "unknown_equipment", "Electrostatic precipitator", "소각 배가스 장치는 거의 unknown + 글자"),
    ])

    gallery("G5_ancillary", "보조 장치·generic·unknown·계측", [
        ("p17", (316, 96, 346, 122), U, "pump", "펌프 (수로 안 기호)", "작아도 친다"),
        ("p02", (804, 274, 834, 304), U, "pump", "펌프 (RAS)", "원 + 꼬리"),
        ("x2", (1122, 663, 1196, 738), U, "pump", "P 원 (특허)", "P가 적힌 원 = 펌프"),
        ("x1", (185, 318, 230, 340), U, "pump", "펌프 (3D 그림)", "파란 모터 모양"),
        ("p50", (60, 265, 95, 300), U, "blower", "Fluidising air fan", "팬·송풍기 = blower"),
        ("x3", (880, 1230, 990, 1310), U, "blower", "팬 기호 (달팽이 모양)", ""),
        ("x1", (205, 60, 250, 100), U, "storage_tank", "Collection Tank", "약품·저류 탱크"),
        ("x1", (118, 88, 150, 125), U, "storage_tank", "50 % NaOH 탱크", "약품 탱크도 장치. 선은 컴퓨터가 약품으로 앎"),
        ("p17", (610, 238, 662, 272), IN, "instrument", "Flowmeter", "계측기·센서 태그"),
        ("p02", (655, 60, 705, 100), IN, "instrument", "DO·NH4 프로브", "탱크 위 작은 센서 태그"),
        ("x2", (1401, 291, 1482, 409), G, "process_unit_generic", "번호만 있는 상자 '104'", "label_text='104', l1_hint=unknown"),
        ("p01", (65, 139, 128, 186), G, "process_unit_generic", "'Biological Treatment' 상자", "단계 이름뿐 → generic, l1_hint=secondary"),
        ("p53", (378, 35, 590, 135), G, "unknown_equipment", "Odour control (biofilter)", "탈취는 목록에 없음 → unknown + 글자"),
        ("x5", (148, 265, 228, 318), G, "unknown_equipment", "Oxygenation", "산소 녹이는 장치. l1_hint=secondary"),
        ("p50", (755, 185, 830, 290), G, "unknown_equipment", "Tertiary bag filter (가스)", "가스 필터는 filtration_unit 아님"),
        ("p50", (660, 95, 705, 130), G, "unknown_equipment", "열교환기", "Hot water 기호"),
    ])

    gallery("G6_connection", "연결 요소 — 단자(io_terminal)·분기·합류", [
        ("x4", (15, 140, 82, 186), IO, "io_terminal", "원수 → io_role=raw_influent", "그림 밖에서 들어오는 끝"),
        ("p10", (18, 22, 248, 70), IO, "io_terminal", "Wastewater 상자 → raw_influent", "상자로 그려도 단자"),
        ("p48", (20, 58, 190, 138), IO, "io_terminal", "Raw Water 글자+선 시작", "글자 포함해서 박스"),
        ("x4", (858, 140, 932, 186), IO, "io_terminal", "방류 → effluent", ""),
        ("p34", (8, 330, 72, 388), IO, "io_terminal", "Submarine Diffusers → effluent", "바다 방류"),
        ("x4", (682, 420, 750, 470), IO, "io_terminal", "처분 → solids_disposal", "슬러지 반출"),
        ("p16", (680, 148, 762, 200), IO, "io_terminal", "Bio solids → solids_disposal", ""),
        ("x4", (585, 20, 692, 78), IO, "io_terminal", "PAC·NaOH 약품 화살표 → chemical_source", "장치 아님. 시작점만 단자", [((634, 108, 650, 124), J)]),
        ("x1", (125, 185, 180, 205), IO, "io_terminal", "Perlite 투입 → chemical_source", "+ 들어가는 데 junction_merge"),
        ("p50", (40, 150, 120, 175), IO, "io_terminal", "Sludge feed → continuation", "다른 그림에서 오는 것"),
        ("p44", (120, 255, 180, 275), IO, "io_terminal", "Biogas → biogas_use", ""),
        ("p50", (960, 140, 990, 320), IO, "io_terminal", "굴뚝 → off_gas_out", ""),
        ("p48", (640, 325, 670, 355), J, "junction_split", "반송·폐기가 갈라지는 점", "선이 갈라지는 곳에 작은 박스"),
        ("p23", (400, 290, 445, 325), J, "junction_split", "분배 상자 (70 % Q / 30 % Q)", "상자로 그려진 분기도 junction"),
        ("x5", (348, 283, 362, 297), J, "junction_merge", "유입 + 반송이 합쳐지는 점", "확대해서 그린다"),
        ("x4", (634, 108, 650, 124), J, "junction_merge", "약품이 들어가는 점", "약품 단자 → 합류점 → 장치"),
    ])

    gallery("G7_zones", "구역(zone) — 한 탱크 안의 칸", [
        ("x4", (348, 55, 472, 125), P, "process_unit_generic (부모)", "생물반응조 전체", "l1_hint=secondary, parent_of로 칸 3개 연결",
         [((352, 62, 383, 120), Z), ((386, 62, 421, 120), Z), ((424, 62, 468, 120), Z)]),
        ("x4", (352, 62, 383, 120), Z, "anaerobic_zone", "혐기조 칸 (is_zone 체크)", "칸마다 박스 하나"),
        ("p23", (560, 5, 965, 150), P, "aerobic_zone (산화구)", "Anoxic + Aerobic 한 수로", "산화구는 한 박스 + 메모",
         [((600, 15, 840, 65), Z), ((600, 70, 840, 145), Z)]),
        ("p44", (268, 98, 460, 160), P, "process_unit_generic (부모)", "Anoxic/Aerobic Zones", "격자 칸 anoxic, 빈 칸 aerobic",
         [((270, 100, 330, 158), Z), ((330, 100, 458, 158), Z)]),
        ("p17", (340, 418, 582, 512), P, "aerobic_zone (부모)", "Aeration tank + Selector", "Selector 칸은 anaerobic/anoxic 구역",
         [((545, 425, 580, 505), Z)]),
        ("p02", (592, 112, 940, 218), NO, "구역 아님", "따로 그려진 CSTR 6개", "탱크가 분리돼 있으면 부모 없이 6개만",
         [((592, 112, 634, 218), Z), ((650, 112, 700, 218), Z)]),
    ], cols=3, cell_w=445)

    gallery("G8_not_annotated", "안 치는 것", [
        ("x4", (780, 430, 950, 562), NO, "범례", "범례 상자", "선 종류 설명. 안 친다"),
        ("p02", (85, 378, 960, 505), NO, "범례", "LEGEND", ""),
        ("p23", (0, 555, 1075, 598), NO, "제목·캡션", "그림 제목 줄", ""),
        ("p17", (100, 205, 200, 250), NO, "표시 점", "Sampling points 빨간 점", "장치가 아니다"),
        ("p53", (350, 5, 410, 50), NO, "번호 원", "순번 ①②③", "쉬운 버전에서는 글자도 안 친다"),
        ("p48", (10, 90, 110, 140), NO, "흐름 글자", "'Q, SS' 같은 수식·변수", "글자는 21~60번에서 안 친다"),
        ("x2", (223, 793, 341, 1525), NO, "제목", "PROCESS FLOW DIAGRAM 세로 글자", ""),
        ("p34", (280, 360, 420, 427), NO, "로고", "기관 로고", ""),
    ])

    gallery("G9_lines", "선 종류 — 라벨은 예외만", [
        ("p53", (40, 775, 850, 800), NO, "선 종류 범례", "실선·점선·일점쇄선·점선", "종류(물/슬러지)는 컴퓨터가 채운다"),
        ("p53", (590, 230, 680, 270), NO, "style:dashed", "점선 흐름 (Wastewater)", "선 긋고 관계 라벨 style:dashed"),
        ("x4", (200, 300, 760, 345), NO, "style:dashed", "반류수 계통 (하늘색 점선)", "style:dashed"),
        ("p23", (330, 135, 440, 300), NO, "no_arrow", "RAS 점선, 화살촉 없음", "방향이 글로만 있으면 no_arrow"),
        ("p01", (120, 80, 330, 112), NO, "optional", "(Optional) 점선", "style:dashed + optional"),
        ("p48", (180, 180, 660, 350), NO, "라벨 없음", "보통 실선 + 화살촉", "라벨 안 고름. 선만 긋는다"),
    ], cols=3, cell_w=445)


# ----------------------------------------------------------------------------- pilot image 1 states
def pilot1_states():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from make_manual_figures import UNITS, TEXTS, STREAMS, IO, JUNCTIONS, ARROWS, pilot1  # noqa: E402
    GC = {"process_unit_generic": C["generic"]}

    def base():
        im, S = pilot1()
        return im, S, ImageDraw.Draw(im)

    def units(d, S):
        for i, (x0, y0, x1, y1, cls, _) in enumerate(UNITS, 1):
            col = GC.get(cls, C["unit"])
            d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=col, width=4)
            d.rectangle([x0 * S - 2, y0 * S - 26, x0 * S + 26, y0 * S], fill=col)
            d.text((x0 * S + 5, y0 * S - 25), str(i), fill="white", font=font(18, True))

    def conn(d, S, full=False):
        for (x0, y0, x1, y1, _) in IO:
            d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline=C["io"], width=4)
        for (x, y, kind) in JUNCTIONS:
            d.rectangle([(x - 5) * S, (y - 5) * S, (x + 5) * S, (y + 5) * S], outline=C["junction"], width=4)
        if full:
            for (x0, y0, x1, y1, _) in TEXTS:
                d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline="#2C5F8A", width=2)
            for (x0, y0, x1, y1, _) in STREAMS:
                d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], outline="#7A3E9D", width=2)
            for (x, y) in ARROWS:
                d.rectangle([(x - 4) * S, (y - 4) * S, (x + 4) * S, (y + 4) * S], outline=C["junction"], width=2)

    def legend(im, lines):
        W = im.width
        pad = Image.new("RGB", (W, 30 + 26 * len(lines)), "white")
        d = ImageDraw.Draw(pad)
        for i, (col, txt) in enumerate(lines):
            d.rectangle([14, 12 + i * 26, 34, 32 + i * 26], outline=col, width=3)
            d.text((44, 10 + i * 26), txt, fill="#1B2A33", font=font(16))
        out = Image.new("RGB", (W, im.height + pad.height), "white")
        out.paste(im, (0, 0)); out.paste(pad, (0, im.height))
        return out

    im, S, d = base(); units(d, S)
    legend(im, [(C["unit"], "장치 박스 8개: ① generic(Preliminary Treatment) ② primary_clarifier ③ generic(Biological Treatment) ④ secondary_clarifier"),
                (C["generic"], "⑤ disinfection_unit ⑥ filtration_unit ⑦ pump ⑧ biofilm_reactor/submerged_biofilter   (회색 = generic, l1_hint 기록)")]).save(OUT / "S1_units.png")
    im, S, d = base(); units(d, S); conn(d, S)
    legend(im, [(C["io"], "io_terminal: Backwash To Solids Processing (continuation)"),
                (C["junction"], "junction_split 2개 (WWF 갈라짐, Backwash 갈라짐) · junction_merge 2개 (Backwash 들어감, 소독조 앞)")]).save(OUT / "S2_lite.png")
    im, S, d = base(); units(d, S); conn(d, S, full=True)
    legend(im, [("#2C5F8A", "text_label 8개 (장치 이름·설명 글자)  ·  stream_label 3개 (선 옆 흐름 이름, 보라)"),
                (C["junction"], "arrowhead 10개 (화살촉마다 작은 박스)  — 1~20번 완전판에서만")]).save(OUT / "S2_full.png")
    print("saved S1_units, S2_lite, S2_full")


# ----------------------------------------------------------------------------- practice answer keys
PRACTICE = {
    1: ("연습 1 — 산업폐수 처리장 3D 그림 (pictorial)", [
        ((10, 14, 132, 28), IO, "io raw_influent"), ((10, 33, 120, 47), IO, "io raw_influent"), ((10, 51, 136, 65), IO, "io raw_influent"),
        ((205, 60, 250, 100), U, "storage_tank"), ((118, 88, 150, 125), U, "storage_tank"), ((303, 88, 335, 125), U, "storage_tank"),
        ((190, 105, 222, 125), U, "pump"), ((112, 133, 135, 150), U, "pump"), ((312, 133, 335, 150), U, "pump"),
        ((55, 150, 105, 172), IO, "io continuation"), ((125, 185, 180, 205), IO, "io chemical_source"),
        ((160, 195, 215, 245), U, "chemical_treatment_unit"), ((258, 195, 305, 245), U, "chemical_treatment_unit"),
        ((420, 170, 470, 225), U, "storage_tank"), ((505, 160, 555, 180), IO, "io continuation"), ((400, 250, 445, 275), U, "pump"),
        ((470, 250, 560, 300), U, "membrane_unit"), ((575, 290, 605, 312), U, "pump"), ((185, 318, 230, 340), U, "pump"),
        ((270, 330, 330, 380), U, "filtration_unit"), ((612, 340, 680, 420), U, "storage_tank"), ((618, 425, 655, 440), IO, "io reclaimed_water_out"),
    ], ["약품 탱크(NaOH·HCl·RO Cleaning)는 storage_tank, 거기서 나가는 선은 컴퓨터가 약품으로 안다.",
        "Neutralization·Precoat = chemical_treatment_unit (약품 처리 탱크, 그림형이니 pictorial).",
        "Kelly Filter = filtration_unit, RO = membrane_unit, Collection Tank = storage_tank. 펌프는 전부.",
        "폐수 세 줄 = raw_influent 단자 3개, Drinking Water = continuation + 메모, Perlite = chemical_source 단자 + 합류점.",
        "그림 속성: C_pictorial · en · 1. 모르는 장치는 범주(필터·막·탱크·펌프)로, 정말 모르면 unknown + 글자."]),
    2: ("연습 2 — 미국 특허 FIG. 3 (글자 상자, 번호)", [
        ((506, 279, 583, 521), IO, "io effluent (Permeate)"), ((632, 372, 1190, 639), U, "mbr_unit"),
        ((1122, 663, 1196, 738), U, "pump"), ((803, 775, 1190, 1228), Z, "aerobic_zone (is_zone)"),
        ((688, 1228, 763, 1302), U, "pump"), ((803, 1333, 1190, 1693), Z, "anoxic_zone (is_zone)"),
        ((723, 1482, 779, 1544), G, "generic '80'"), ((564, 1488, 645, 1662), IO, "io raw_influent (Inflow)"),
        ((564, 1736, 645, 2015), U, "screen"), ((885, 2045, 965, 2125), U, "pump"), ((1340, 1897, 1686, 2139), U, "pump_station"),
        ((1401, 291, 1482, 409), G, "generic '104'"), ((1538, 570, 1618, 688), G, "generic '132'"),
    ], ["Mixed Anoxic Tank·Aerobic Tank는 따로 그려져 있으니 parent_of 없이 칸 두 개, is_zone 체크.",
        "Membrane Tank = mbr_unit (Return flow로 돌려보냄). Permeate 끝 = effluent 단자. Sewer Lift Station = pump_station.",
        "글자 없는 작은 상자 80·104·132 = process_unit_generic, l1_hint=unknown, label_text에 번호.",
        "INFLOW·GRAVITY FLOW·RETURN FLOW·SLUDGE RETURN 같은 글자 상자는 흐름 이름이지 장치가 아니다 (INFLOW만 단자).",
        "Return flow·Sludge Return 선은 둘 다 긋는다. 종류는 컴퓨터가 채운다. 그림 속성: A_box · en · 1."]),
    3: ("연습 3 — 다단 소각로 흐름도 (슬러지·가스 라인)", [
        ((245, 555, 565, 1320), U, "drying_incineration_unit"), ((745, 365, 1000, 555), G, "unknown 'Heat recovery boiler'"),
        ((1255, 555, 1320, 745), G, "unknown 'Precooler and venturi'"), ((1380, 360, 1510, 870), G, "unknown 'Wet scrubber'"),
        ((1395, 200, 1500, 355), U, "blower (induced draft fan)"), ((880, 1230, 990, 1310), U, "blower"), ((20, 1490, 125, 1560), U, "blower"),
        ((1760, 720, 1870, 810), U, "pump"), ((1640, 1165, 1750, 1250), U, "pump"),
        ((0, 655, 160, 715), IO, "io continuation (Sludge feed)"), ((1355, 10, 1540, 40), IO, "io off_gas_out"),
        ((590, 1405, 760, 1450), IO, "io solids_disposal (Ash)"), ((620, 965, 880, 1040), IO, "io chemical_source (Fuel)"),
        ((1030, 1290, 1610, 1330), IO, "io chemical_source (Power)+메모"), ((1520, 960, 1700, 1010), IO, "io effluent (Drain)"),
    ], ["소각로 = drying_incineration_unit (글자 보고 알았으니 box). 보일러·벤투리·스크러버는 목록에 없으니 unknown + l1_hint=sludge + 글자 그대로.",
        "팬 = blower. 물 넣는 펌프 기호 = pump.",
        "그림 밖으로 드나드는 끝은 전부 io_terminal: Gas Exhaust=off_gas_out, Ash=solids_disposal, Sludge Feed=continuation, Fuel·Power·Scrubber Water=chemical_source + 메모.",
        "RADIATION·RECOVERABLE HEAT 화살표는 열이지 물질이 아니다 → 안 친다, 메모만. 그림 속성: A_box · en · 1."]),
    4: ("연습 4 — 한국 지자체 공정도 (그림형, 두 계열)", [
        ((15, 140, 82, 186), IO, "io raw_influent"), ((100, 120, 235, 192), U, "pump_station (부모)"), ((105, 135, 165, 185), U, "grit_chamber (자식)"),
        ((257, 70, 330, 122), U, "primary_clarifier"), ((348, 55, 472, 125), G, "generic 생물반응조 (부모)"),
        ((352, 62, 383, 120), Z, "anaerobic_zone"), ((386, 62, 421, 120), Z, "anoxic_zone"), ((424, 62, 468, 120), Z, "aerobic_zone"),
        ((472, 70, 548, 122), U, "secondary_clarifier"),
        ((257, 215, 330, 267), U, "primary_clarifier"), ((348, 200, 472, 270), G, "generic 생물반응조 (부모)"),
        ((352, 207, 400, 265), Z, "anoxic_zone (탈질조)"), ((403, 207, 468, 265), Z, "aerobic_zone"), ((472, 215, 548, 267), U, "secondary_clarifier"),
        ((588, 118, 692, 198), U, "secondary_clarifier '응집침전지'"), ((700, 130, 776, 188), U, "filtration_unit"), ((782, 130, 852, 182), U, "disinfection_unit"),
        ((858, 140, 932, 186), IO, "io effluent"), ((585, 20, 692, 78), IO, "io chemical_source"), ((634, 108, 650, 124), J, "junction_merge"),
        ((612, 255, 684, 300), U, "thickener"), ((190, 350, 272, 422), U, "sidestream_reactor"), ((312, 388, 392, 432), U, "thickener"),
        ((415, 375, 482, 447), U, "digester"), ((536, 385, 622, 447), U, "dewatering_unit"), ((682, 420, 750, 470), IO, "io solids_disposal"),
        ((40, 470, 130, 500), IO, "io external_waste_in (연계처리)"),
    ], ["계열이 둘이면 둘 다 친다. process_configuration 칸에 '1단계 A2O(개량), 2단계 MLE' 원문 그대로.",
        "생물반응조 전체 = generic(l1_hint=secondary) 부모, 안의 혐기·무산소·호기 칸 = *_zone + is_zone, 부모→칸 parent_of.",
        "침사지 및 유입펌프장 한 덩어리 = 바깥 pump_station, 안쪽 침사지 grit_chamber 자식.",
        "PAC·Alum·폴리머 주황 화살표 = 장치 아님. 시작점 io_terminal(chemical_source) → 들어가는 점 junction_merge → 장치.",
        "점선·일점쇄선은 선 긋고 style:dashed. 범례 상자는 안 친다. 그림 속성: C_pictorial · ko · 1."]),
    5: ("연습 5 — 유동상 반응기 파일럿 (기호형)", [
        ((12, 10, 75, 355), U, "biofilm_reactor/fluidized_expanded_bed"), ((225, 25, 305, 105), U, "secondary_clarifier"),
        ((148, 265, 228, 318), G, "unknown 'Oxygenation'"), ((375, 282, 462, 300), IO, "io raw_influent"),
        ((400, 38, 470, 72), IO, "io effluent"), ((238, 172, 290, 192), IO, "io solids_disposal"),
        ((348, 41, 362, 55), J, "junction_split"), ((348, 283, 362, 297), J, "junction_merge"),
    ], ["Fluidized bed reactor = biofilm_reactor/fluidized_expanded_bed (슬래시 뒤까지). 원뿔 = secondary_clarifier (symbol, certain).",
        "Oxygenation = unknown_equipment, l1_hint=secondary, label_text='Oxygenation'.",
        "선: 유입→합류점→Oxygenation→반응기→침전지→분기점→방류, 분기점→합류점(Recycled effluent), 침전지→Sludge 단자.",
        "그림 속성: B_symbol · en · 1."]),
}


def practice_keys():
    for no, (title, boxes, notes) in PRACTICE.items():
        im = img(f"x{no}").copy()
        S = 1.0
        if im.width < 900:
            S = 900 / im.width
            im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS)
        elif im.width > 1500:
            S = 1500 / im.width
            im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        fs = 15
        for i, (b, col, lab) in enumerate(boxes, 1):
            r = [b[0] * S, b[1] * S, b[2] * S, b[3] * S]
            d.rectangle(r, outline=col, width=3)
            tw = d.textlength(str(i), font=font(fs, True)) + 8
            d.rectangle([r[0], r[1] - fs - 6, r[0] + tw, r[1]], fill=col)
            d.text((r[0] + 4, r[1] - fs - 5), str(i), fill="white", font=font(fs, True))
        # legend block
        cols = 3
        rows = (len(boxes) + cols - 1) // cols
        lh = 22
        pad = Image.new("RGB", (im.width, 44 + rows * lh + 12 + len(notes) * 24 + 10), "white")
        dp = ImageDraw.Draw(pad)
        dp.text((12, 10), title, fill="#1B2A33", font=font(17, True))
        cw = im.width // cols
        for i, (b, col, lab) in enumerate(boxes, 1):
            r, c = divmod(i - 1, cols)
            x, y = 12 + c * cw, 44 + r * lh
            dp.rectangle([x, y + 4, x + 14, y + 18], fill=col)
            dp.text((x + 20, y), f"{i}  {lab}", fill="#1B2A33", font=font(13, mono=lab.isascii()))
        y0 = 44 + rows * lh + 12
        for i, n in enumerate(notes):
            dp.text((12, y0 + i * 24), "• " + n, fill="#333333", font=font(12.5))
        out = Image.new("RGB", (im.width, im.height + pad.height), "white")
        out.paste(im, (0, 0)); out.paste(pad, (0, im.height))
        out.save(OUT / f"PR{no}.png")
        print("saved", f"PR{no}", out.size)


if __name__ == "__main__":
    galleries()
    pilot1_states()
    practice_keys()
