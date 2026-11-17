"""1:1 hybrid editable reconstruction of V4 Fig. 1 candidate (candidate-b-v4-best.png).
Raster illustrations use exterior flood-fill alpha matting and text-glyph inpainting;
all cards, boxes, arrows, neurons, region chips, balance meter and typography are native PowerPoint objects.
"""
from pathlib import Path
from collections import deque
import json
import hashlib
import numpy as np
from scipy import ndimage
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement

R = Path(__file__).resolve().parents[1]
O = R / 'reports/phase8/figures'
A = O / 'fig1-assets'
A.mkdir(exist_ok=True)
source = O / 'fig1-candidates/candidate-b-v4-best.png'
im = Image.open(source).convert('RGBA')
W, H = im.size  # 1568 x 1003
SX = W / 1568.0
SY = H / 1003.0

pr = Presentation()
pr.slide_width = Inches(15.68)
pr.slide_height = Inches(10.03)
sl = pr.slides.add_slide(pr.slide_layouts[6])
sl.background.fill.solid()
sl.background.fill.fore_color.rgb = RGBColor(255, 255, 255)

assets = {}
texts = []
arrows = []


def flood_soft_alpha(rgba_arr, bg_thresh=244, feather=1.8):
    """Apply exterior border connected-component flood-fill alpha matting while keeping interior highlights intact."""
    h, w, _ = rgba_arr.shape
    rgb = rgba_arr[:, :, :3]
    is_bg = np.all(rgb >= bg_thresh, axis=2)
    ext = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        if is_bg[0, x]:
            ext[0, x] = True
            q.append((0, x))
        if is_bg[h - 1, x] and not ext[h - 1, x]:
            ext[h - 1, x] = True
            q.append((h - 1, x))
    for y in range(h):
        if is_bg[y, 0] and not ext[y, 0]:
            ext[y, 0] = True
            q.append((y, 0))
        if is_bg[y, w - 1] and not ext[y, w - 1]:
            ext[y, w - 1] = True
            q.append((y, w - 1))
    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not ext[ny, nx] and is_bg[ny, nx]:
                ext[ny, nx] = True
                q.append((ny, nx))
    dist = ndimage.distance_transform_edt(~ext)
    alpha = np.clip(dist / feather, 0.0, 1.0)
    alpha[ext] = 0.0
    out = rgba_arr.copy()
    out[:, :, 3] = np.round(alpha * 255.0).astype(np.uint8)
    return out


def _harmonic_infill(rgb_arr, mask):
    """Smoothly infill masked pixels from surrounding valid pixels via multi-step masked diffusion."""
    out = rgb_arr.astype(np.float32).copy()
    valid = ~mask
    if not mask.any() or not valid.any():
        return rgb_arr
    # Initialize masked pixels with nearest valid pixel colors, then smoothly diffuse inside mask
    _, idx = ndimage.distance_transform_edt(mask, return_indices=True)
    for c in range(3):
        out[:, :, c][mask] = out[:, :, c][idx[0][mask], idx[1][mask]]
    kernel = np.array([[0.05, 0.20, 0.05], [0.20, 0.0, 0.20], [0.05, 0.20, 0.05]], dtype=np.float32)
    for _ in range(18):
        for c in range(3):
            blur = ndimage.convolve(out[:, :, c], kernel, mode='nearest')
            out[:, :, c][mask] = blur[mask]
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def inpaint_dark_glyphs(rgba_arr, rel_boxes, lum_thresh=115, dilate_px=2):
    """Erase raster dark text glyphs inside relative boxes via local smooth infill."""
    mask = np.zeros(rgba_arr.shape[:2], dtype=bool)
    for x1, y1, x2, y2 in rel_boxes:
        sub = rgba_arr[y1:y2, x1:x2, :3]
        dark = np.all(sub < lum_thresh, axis=2)
        mask[y1:y2, x1:x2][dark] = True
    mask = ndimage.binary_dilation(mask, iterations=dilate_px)
    out = rgba_arr.copy()
    out[:, :, :3] = _harmonic_infill(rgba_arr[:, :, :3], mask)
    return out


def inpaint_pill_boxes(rgba_arr, rel_boxes, pad=2):
    """Erase entire small pill labels inside an illustration box before replacing them with native shapes."""
    mask = np.zeros(rgba_arr.shape[:2], dtype=bool)
    for x1, y1, x2, y2 in rel_boxes:
        mask[max(0, y1 - pad):y2 + pad, max(0, x1 - pad):x2 + pad] = True
    out = rgba_arr.copy()
    out[:, :, :3] = _harmonic_infill(rgba_arr[:, :, :3], mask)
    return out


def soft_edge_fade(rgba_arr, top=0, bottom=0, left=0, right=0):
    """Apply smooth edge alpha fade along specified edges so illustrations blend softly into panel fills."""
    h, w, _ = rgba_arr.shape
    a = rgba_arr[:, :, 3].astype(np.float32) / 255.0
    if top > 0:
        a[:top, :] *= np.linspace(0.0, 1.0, top)[:, None]
    if bottom > 0:
        a[-bottom:, :] *= np.linspace(1.0, 0.0, bottom)[:, None]
    if left > 0:
        a[:, :left] *= np.linspace(0.0, 1.0, left)[None, :]
    if right > 0:
        a[:, -right:] *= np.linspace(1.0, 0.0, right)[None, :]
    out = rgba_arr.copy()
    out[:, :, 3] = np.round(np.clip(a, 0.0, 1.0) * 255.0).astype(np.uint8)
    return out


def pic(name, box, x, y, w, h, soft_bg=False, bg_thresh=244, inpaint_dark=None, inpaint_pills=None, edge_fade=None):
    px_box = tuple(round(v * (SX if i % 2 == 0 else SY)) for i, v in enumerate(box))
    crop = im.crop(px_box)
    arr = np.array(crop)
    if inpaint_pills:
        arr = inpaint_pill_boxes(arr, inpaint_pills)
    if inpaint_dark:
        arr = inpaint_dark_glyphs(arr, inpaint_dark)
    if soft_bg:
        arr = flood_soft_alpha(arr, bg_thresh=bg_thresh)
    if edge_fade:
        arr = soft_edge_fade(arr, **edge_fade)
    f = A / (name + '.png')
    Image.fromarray(arr, mode='RGBA').save(f)
    assets[name] = {'source_box': box, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
    sl.shapes.add_picture(str(f), Inches(x / 100.0), Inches(y / 100.0), width=Inches(w / 100.0), height=Inches(h / 100.0))


def txt(x, y, w, h, s, size=13, bold=False, italic=False, align='left', color='000000', anchor='top'):
    sh = sl.shapes.add_textbox(Inches(x / 100.0), Inches(y / 100.0), Inches(w / 100.0), Inches(h / 100.0))
    tf = sh.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = {'top': MSO_ANCHOR.TOP, 'middle': MSO_ANCHOR.MIDDLE, 'bottom': MSO_ANCHOR.BOTTOM}[anchor]
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    tf.margin_top = Pt(1)
    tf.margin_bottom = Pt(1)
    rgb = RGBColor.from_string(color)
    for i, line_str in enumerate(s.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {'left': PP_ALIGN.LEFT, 'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT}[align]
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        p.font.name = 'Times New Roman'
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = rgb
        p.text = line_str
        for rr in p.runs:
            rr.font.name = 'Times New Roman'
            rr.font.size = Pt(size)
            rr.font.bold = bold
            rr.font.italic = italic
            rr.font.color.rgb = rgb
    texts.append(s)
    return sh


def card(x, y, w, h, fill='FFFFFF', edge='4C7A99', lw=1.2, radius=0.08):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius > 0 else MSO_SHAPE.RECTANGLE
    sh = sl.shapes.add_shape(kind, Inches(x / 100.0), Inches(y / 100.0), Inches(w / 100.0), Inches(h / 100.0))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if edge is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = RGBColor.from_string(edge)
        sh.line.width = Pt(lw)
    if radius > 0:
        sh.adjustments[0] = radius
    return sh


def circle(cx, cy, d, fill='FFFFFF', edge='000000', lw=1.0):
    sh = sl.shapes.add_shape(MSO_SHAPE.OVAL, Inches((cx - d / 2) / 100.0), Inches((cy - d / 2) / 100.0), Inches(d / 100.0), Inches(d / 100.0))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if edge is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = RGBColor.from_string(edge)
        sh.line.width = Pt(lw)
    return sh


def line(x1, y1, x2, y2, arrow=True, width=1.4, color='000000', dash=False):
    sh = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1 / 100.0), Inches(y1 / 100.0), Inches(x2 / 100.0), Inches(y2 / 100.0))
    sh.line.color.rgb = RGBColor.from_string(color)
    sh.line.width = Pt(width)
    ln = sh._element.spPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ln')
    if dash:
        pd = OxmlElement('a:prstDash')
        pd.set('val', 'dash')
        ln.append(pd)
    if arrow:
        end = OxmlElement('a:tailEnd')
        end.set('type', 'triangle')
        end.set('w', 'med')
        end.set('len', 'med')
        ln.append(end)
    arrows.append([x1, y1, x2, y2, arrow])
    return sh


def route(points, arrow=True, width=1.4, color='000000'):
    for i, (p, q) in enumerate(zip(points, points[1:])):
        line(*p, *q, arrow=(arrow and i == len(points) - 2), width=width, color=color)


# ==============================================================================
# 1. Top-Left Field Observation & Soil Physical Anchor Module
# ==============================================================================
card(20, 39, 492, 398, fill='EBF3FA', edge='4C7A99', lw=1.4, radius=0.04)
# Inpaint embedded text pills inside weather-field before overlaying native rounded cards
pic(
    'weather-field',
    (25, 44, 507, 432),
    25, 44, 482, 388,
    inpaint_pills=[(192, 16, 452, 86), (200, 92, 438, 170), (152, 310, 464, 380)],
    edge_fade={'top': 6, 'bottom': 6, 'left': 6, 'right': 6},
)
card(216, 60, 260, 68, fill='F2F6FA', edge='4C7A99', lw=1.1, radius=0.35)
txt(220, 64, 252, 60, 'Weather history', size=16, bold=True, align='center', anchor='middle')

card(228, 138, 234, 72, fill='F2F6FA', edge='4C7A99', lw=1.1, radius=0.25)
txt(232, 142, 226, 64, 'Crop stage &\ndose history', size=15, bold=True, align='center', anchor='middle')

card(180, 356, 306, 56, fill='EFE7DC', edge='9A8876', lw=1.1, radius=0.40)
txt(184, 360, 298, 48, 'Soil physical anchor', size=15, bold=True, align='center', anchor='middle')


# ==============================================================================
# 2. Agent 1: Spatial Twin Specialist (Top-Right Card)
# ==============================================================================
card(544, 14, 1022, 398, fill='EDF4FB', edge='4C7A99', lw=1.4, radius=0.03)
txt(556, 20, 998, 42, 'Agent 1: Spatial Twin Specialist', size=21, bold=True, align='center', anchor='middle')

# Satellite & Earth illustration (exterior transparent)
pic('satellite-earth-raster', (562, 65, 882, 242), 564, 65, 316, 175, soft_bg=True, bg_thresh=232)

# PyTorch MLP sub-card + editable neural circuit
card(912, 72, 294, 180, fill='E5EFF8', edge='4C7A99', lw=1.2, radius=0.06)
txt(920, 77, 278, 44, 'PyTorch MLP\n(3 frozen seeds)', size=15, bold=True, align='center', anchor='middle')

layer_xs = [950, 1018, 1094, 1166]
layer_counts = [3, 4, 4, 3]
node_coords = []
for lx, nc in zip(layer_xs, layer_counts):
    y0 = 158 - (nc - 1) * 16 / 2.0
    ys = [y0 + k * 16 for k in range(nc)]
    node_coords.append([(lx, yy) for yy in ys])
for a_pts, b_pts in zip(node_coords, node_coords[1:]):
    for x1, y1 in a_pts:
        for x2, y2 in b_pts:
            line(x1, y1, x2, y2, arrow=False, width=0.55, color='4C7A99')
for pts in node_coords:
    for nx, ny in pts:
        circle(nx, ny, 11, fill='9BBCD6', edge='2F4F66', lw=0.7)
# Subtle ellipsis dots in hidden layer gap
for mx in [1050, 1056, 1062]:
    circle(mx, 158, 3.5, fill='2F4F66', edge=None)

txt(920, 198, 278, 48, '36 → 96 → 96 → 3\n13,155 parameters', size=14, bold=True, align='center', anchor='middle')

# Summing node (+)
circle(1242, 236, 36, fill='FFFFFF', edge='2B3A42', lw=1.2)
txt(1224, 217, 36, 36, '+', size=20, bold=True, align='center', anchor='middle')

# Private AlphaEarth 64-D & Static3 emblems + native labels
pic('private-raster', (576, 250, 682, 322), 576, 252, 98, 68, soft_bg=True, bg_thresh=232)
card(680, 254, 134, 62, fill='EEF5EC', edge='5E9680', lw=1.1, radius=0.08)
txt(684, 258, 126, 54, 'Private\nAlphaEarth\n64-D', size=13, bold=True, align='center', anchor='middle')

pic('soil-static3', (576, 326, 682, 396), 576, 328, 98, 66, soft_bg=True, bg_thresh=232)
card(680, 336, 134, 48, fill='EEF5EC', edge='5E9680', lw=1.1, radius=0.08)
txt(684, 340, 126, 40, 'Static3', size=15, bold=True, align='center', anchor='middle')

# Adapter card
card(852, 278, 178, 72, fill='E8EFE3', edge='5E9680', lw=1.2, radius=0.08)
txt(858, 282, 166, 64, 't − 1 anomaly\n→ PCA + Ridge\n≤ 4-D', size=13, bold=True, align='center', anchor='middle')

# Region bar (NL | CN | US | FR | AU)
reg_w = 53
for k, rlab in enumerate(['NL', 'CN', 'US', 'FR', 'AU']):
    card(918 + k * reg_w, 368, reg_w, 26, fill='FFFFFF', edge='5E7685', lw=0.9, radius=0.0)
    txt(918 + k * reg_w, 368, reg_w, 26, rlab, size=13, bold=True, align='center', anchor='middle')

# Output cards on right side of Agent 1
card(1276, 96, 272, 42, fill='E5EFF8', edge='4C7A99', lw=1.1, radius=0.14)
txt(1280, 99, 264, 36, 'Yield · Grain N · Executed N', size=14, bold=True, align='center', anchor='middle')

card(1276, 164, 272, 42, fill='E5EFF8', edge='4C7A99', lw=1.1, radius=0.14)
txt(1280, 167, 264, 36, '15 × 32 residuals', size=15, bold=True, align='center', anchor='middle')

card(1276, 254, 272, 66, fill='FAE8E7', edge='B8525A', lw=1.2, radius=0.12)
txt(1280, 260, 264, 54, 'Surplus & NUE', size=18, bold=True, align='center', anchor='middle')

# Agent 1 internal wiring
line(512, 224, 544, 224, arrow=True, width=1.6)
line(882, 160, 912, 160, arrow=True, width=1.5)
route([(1206, 160), (1242, 160), (1242, 218)], arrow=True, width=1.4)
line(814, 285, 852, 285, arrow=True, width=1.4)
route([(814, 360), (1242, 360), (1242, 254)], arrow=True, width=1.4)
route([(1030, 314), (1242, 314), (1242, 254)], arrow=True, width=1.4)
route([(1242, 218), (1242, 117), (1276, 117)], arrow=True, width=1.4)
line(1412, 138, 1412, 164, arrow=True, width=1.4)
line(1412, 206, 1412, 254, arrow=True, width=1.4)


# ==============================================================================
# 3. Left Column Specialists (Agents 2, 3, 4) & Four Coupling Links
# ==============================================================================
# Agent 2: Climate Forecast Specialist
card(4, 468, 464, 192, fill='EDF4FB', edge='4C7A99', lw=1.4, radius=0.04)
txt(14, 474, 444, 34, 'Agent 2: Climate Forecast Specialist', size=17, bold=True, align='center', anchor='middle')
pic('climate-clouds-fan', (14, 512, 294, 650), 14, 512, 280, 138, edge_fade={'top': 4, 'bottom': 4, 'left': 4, 'right': 4})
txt(302, 514, 158, 136, 'TRAIN 1995–2009\nHistorical\n+1.8°C · 450 ppm\n+3.5°C · 550 ppm\nCausal analogs', size=13, bold=False, align='left', anchor='middle')

# Agent 3: Urban Eco-Safety Specialist
card(4, 668, 464, 148, fill='EEF5EC', edge='5E9680', lw=1.4, radius=0.05)
txt(14, 672, 444, 32, 'Agent 3: Urban Eco-Safety Specialist', size=17, bold=True, align='center', anchor='middle')
pic('urban-watershed', (14, 706, 288, 808), 14, 706, 274, 102, edge_fade={'top': 4, 'bottom': 4, 'left': 4, 'right': 4})
txt(292, 708, 168, 98, '0 ≤ S_N ≤ cap\n\n25 / 35 / 40 / 50\nkg N/ha', size=14, bold=True, align='center', anchor='middle')

# Agent 4: Socio-Economic Policy Specialist
card(4, 824, 464, 158, fill='FBEFEE', edge='B8525A', lw=1.4, radius=0.04)
txt(14, 828, 444, 32, 'Agent 4: Socio-Economic Policy Specialist', size=17, bold=True, align='center', anchor='middle')
pic('market-policy-balance', (16, 864, 274, 974), 16, 864, 258, 110, soft_bg=True, bg_thresh=240)
txt(280, 864, 180, 108, 'Price 1× / 2×\nSubsidy / tax\n\n0.50 ≤ NUE ≤ 0.90', size=14, bold=True, align='center', anchor='middle')

# Coupling 1 (Spatial) top -> Agent 5
line(780, 412, 780, 468, arrow=True, width=1.8)
card(792, 418, 224, 34, fill='FFFFFF', edge='4C7A99', lw=1.0, radius=0.30)
txt(796, 420, 216, 30, '1   Spatial Coupling', size=13, bold=True, align='center', anchor='middle')

# Couplings 2, 3, 4 (Left Agents -> Agent 5)
coupling_specs = [
    (562, '2', 'Climate\nCoupling', '4C7A99'),
    (712, '3', 'Eco Safety\nCoupling', '5E9680'),
    (894, '4', 'Economics\nCoupling', 'B8525A'),
]
for cy, num, lab, col in coupling_specs:
    line(468, cy, 566, cy, arrow=True, width=1.8)
    circle(517, cy - 28, 26, fill=col, edge=None)
    txt(504, cy - 41, 26, 26, num, size=13, bold=True, color='FFFFFF', align='center', anchor='middle')
    card(474, cy - 12, 86, 42, fill='FFFFFF', edge=col, lw=0.95, radius=0.18)
    txt(476, cy - 10, 82, 38, lab, size=11, bold=True, align='center', anchor='middle')


# ==============================================================================
# 4. Agent 5: Core Agronomic Control Specialist (Center Module)
# ==============================================================================
card(566, 468, 616, 514, fill='F4F8F2', edge='4A7C59', lw=1.6, radius=0.03)
txt(580, 474, 588, 38, 'Agent 5: Core Agronomic Control Specialist', size=19, bold=True, align='center', anchor='middle')

# Central wheat phenology + soil/droplet artwork (inpaint Rain/Temp words, a1-a3 bottom edges, and crop Tillering/Jointing/Booting pills)
pic(
    'agent5-wheat-roots',
    (578, 552, 1170, 792),
    578, 552, 592, 240,
    inpaint_pills=[
        (36, 0, 556, 22),
        (112, 38, 174, 78),
        (192, 38, 254, 80),
        (312, 38, 384, 80),
        (392, 38, 470, 78),
        (84, 112, 202, 156),
        (302, 112, 400, 156),
        (484, 112, 586, 156),
    ],
    edge_fade={'top': 8, 'bottom': 10, 'left': 6, 'right': 6},
)

# Native action pills a1 -> a2 -> a3 (exactly 1 count each for verify script)
for cx, fill_c, edge_c, lab in [
    (662, 'E5EFF8', '4C7A99', 'a1'),
    (864, 'E5F2E6', '5E9680', 'a2'),
    (1082, 'E5EFF8', '4C7A99', 'a3'),
]:
    card(cx - 38, 516, 76, 34, fill=fill_c, edge=edge_c, lw=1.3, radius=0.45)
    txt(cx - 34, 517, 68, 32, lab, size=17, bold=True, italic=True, align='center', anchor='middle')
line(702, 533, 824, 533, arrow=True, width=1.5)
line(904, 533, 1042, 533, arrow=True, width=1.5)

# Native weather branch labels
txt(684, 588, 72, 34, 'Rain:\nlow', size=11, bold=False, align='center', anchor='middle')
txt(764, 588, 74, 34, 'Rain:\nhigh', size=11, bold=False, align='center', anchor='middle')
txt(894, 588, 74, 34, 'Temp:\ncool', size=11, bold=False, align='center', anchor='middle')
txt(976, 588, 78, 34, 'Temp:\nwarm', size=11, bold=False, align='center', anchor='middle')

# Native phenology pills
for px, pw, plab in [(666, 94, 'Tillering'), (884, 88, 'Jointing'), (1076, 86, 'Booting')]:
    card(px, 672, pw, 26, fill='FFFFFF', edge='5E7685', lw=0.9, radius=0.35)
    txt(px + 2, 673, pw - 4, 24, plab, size=12, bold=True, align='center', anchor='middle')

# Native Nutrient-Safety Corridor Balance Meter
card(584, 796, 580, 114, fill='FBF9F4', edge='C8D1D7', lw=1.0, radius=0.08)
txt(594, 800, 560, 26, 'Nutrient-Safety Corridor Balance Meter', size=15, bold=True, align='center', anchor='middle')
txt(594, 825, 560, 22, '0.50 ≤ NUE ≤ 0.90', size=13, bold=True, align='center', anchor='middle')

# Gradient-free clean semantic meter bar (Left risk | Safe center | Right risk)
card(768, 849, 64, 15, fill='F2CFCB', edge='B8525A', lw=0.8, radius=0.0)
card(832, 849, 86, 15, fill='88B598', edge='4A7C59', lw=0.8, radius=0.0)
card(918, 849, 64, 15, fill='F2CFCB', edge='B8525A', lw=0.8, radius=0.0)
circle(875, 856, 20, fill='E2ECE4', edge='2B3A42', lw=1.5)

# Three policy controller badges inside Balance Meter
card(598, 874, 168, 30, fill='FFFFFF', edge='9BA6AE', lw=0.9, radius=0.35)
txt(602, 876, 160, 26, 'Tier2-Composite', size=13, bold=False, align='center', anchor='middle')

card(780, 874, 190, 32, fill='E5F1E6', edge='4A7C59', lw=1.3, radius=0.35)
txt(784, 876, 182, 28, 'Soft-Coupled', size=14, bold=True, align='center', anchor='middle')

card(984, 874, 166, 30, fill='FFFFFF', edge='9BA6AE', lw=0.9, radius=0.35)
txt(988, 876, 158, 26, 'Archived bare', size=13, bold=False, align='center', anchor='middle')

# Bottom planning objective bar (exact verify string required!)
card(584, 916, 580, 54, fill='FAE8E7', edge='B8525A', lw=1.2, radius=0.14)
txt(
    592, 919, 564, 48,
    'Partial profit + 250 P(active joint) − 300 distance\n2 kg/ha margin · 1.5× upper NUE penalty',
    size=13, bold=True, align='center', anchor='middle',
)


# ==============================================================================
# 5. Execute Dose & External WOFOST81-SNOMIN Referee (Right Column)
# ==============================================================================
card(1196, 558, 128, 76, fill='EEF5EC', edge='5E9680', lw=1.2, radius=0.16)
txt(1200, 562, 120, 68, 'Execute\ncurrent dose', size=14, bold=True, align='center', anchor='middle')

pic('tractor-wheat', (1332, 506, 1566, 672), 1336, 514, 230, 164, soft_bg=True, bg_thresh=240)
line(1182, 596, 1196, 596, arrow=True, width=1.6)
line(1324, 596, 1340, 596, arrow=True, width=1.6)

card(1192, 694, 374, 288, fill='FBEFEE', edge='B8525A', lw=1.4, radius=0.04)
txt(1200, 698, 358, 48, 'External WOFOST81-SNOMIN\nReferee', size=15, bold=True, align='center', anchor='middle')

pic(
    'referee-root-soil',
    (1198, 750, 1356, 970),
    1200, 750, 156, 218,
    soft_bg=True, bg_thresh=240,
)
# Native editable N & C glyphs over soil cycle circles
for cy, lab in [(878, 'N'), (924, 'C')]:
    circle(1274, cy, 30, fill='FFFFFF', edge='2B3A42', lw=1.0)
    txt(1259, cy - 15, 30, 30, lab, size=15, bold=True, align='center', anchor='middle')

for yy, hh, lab in [(756, 42, 'Yield'), (814, 44, 'Native N loss'), (874, 58, 'Daily C/N closure')]:
    card(1364, yy, 188, hh, fill='FFFFFF', edge='9BA6AE', lw=1.0, radius=0.14)
    txt(1368, yy + 2, 180, hh - 4, lab, size=15, bold=True, align='center', anchor='middle')

line(1260, 634, 1260, 694, arrow=True, width=1.6)


# ==============================================================================
# 6. Full-Bleed Reference Slide (Slide 2) & Export
# ==============================================================================
reference = pr.slides.add_slide(pr.slide_layouts[6])
reference.shapes.add_picture(str(source), 0, 0, width=pr.slide_width, height=pr.slide_height)
pr.save(O / 'fig1-architecture.pptx')

(O / 'fig1-assets/asset-manifest.json').write_text(json.dumps({
    'reference': str(source.relative_to(R)),
    'reference_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'assets': assets,
    'native_texts': texts,
    'native_connections': arrows,
    'editable_slide': 1,
    'reference_slide': 2,
    'total_slide_objects': len(sl.shapes),
    'numerical_specialists_not_LLMs': True,
    'referee_outgoing_edges': 0,
    'action_levels': ['a1', 'a2', 'a3'],
}, indent=2))
print(json.dumps({'status': 'BUILT', 'shapes_total': len(sl.shapes), 'assets': len(assets), 'texts': len(texts)}))
