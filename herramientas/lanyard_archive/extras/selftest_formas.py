import numpy as np, cv2, math
import selftest as T, lanyard_core as core

def letters_card(w_mm, h_mm, bump=False, flip=False):
    W, H = int(round(w_mm*T.PPM_S)), int(round(h_mm*T.PPM_S))
    img = np.zeros((H, W, 4), np.uint8); img[..., :3] = (42, 28, 95)
    # fondo con rombos suaves
    for i in range(0, W+H, 90):
        cv2.line(img, (i, 0), (i-H, H), (60, 40, 120, 255), 3)
    cv2.putText(img, "HEALTH", (int(W*.08), int(H*.30)), cv2.FONT_HERSHEY_DUPLEX, W/150, (245,245,245,255), int(W/60), cv2.LINE_AA)
    cv2.putText(img, "TECH2030", (int(W*.08), int(H*.50)), cv2.FONT_HERSHEY_DUPLEX, W/260, (245,245,245,255), int(W/80), cv2.LINE_AA)
    cv2.putText(img, "WE ARE", (int(W*.30), int(H*.16)), cv2.FONT_HERSHEY_DUPLEX, W/300, (245,245,245,255), int(W/110), cv2.LINE_AA)
    img[..., 3] = 255
    m = np.zeros((H, W), np.uint8); r = int(4*T.PPM_S)
    cv2.rectangle(m, (r,0), (W-r,H), 255, -1); cv2.rectangle(m, (0,r), (W,H-r), 255, -1)
    for cx, cy in [(r,r),(W-r,r),(r,H-r),(W-r,H-r)]: cv2.circle(m, (cx,cy), r, 255, -1)
    cv2.circle(m, (W//2, int(9*T.PPM_S)), int(2.6*T.PPM_S), 0, -1)                     # orificio real ø5,2
    img[..., 3] = m
    if bump:                                                                           # bulto de 1,6 mm en el borde derecho
        big = np.zeros((H, W+int(1.6*T.PPM_S), 4), np.uint8); big[:, :W] = img
        big[int(H*.1):int(H*.1)+int(9*T.PPM_S), W:] = (42,28,95,255)
        img = big
    return img

def medal(angle=0.0):
    pts = np.array([(10,0),(30,2),(45,8),(56,22),(48,34),(40,42),(36,60),(28,61),(22,48),(20,34),(8,30),(0,18),(3,6)], np.float32)
    c = pts.mean(0); a = math.radians(angle)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]], np.float32)
    pts = (pts - c) @ R.T
    mn = pts.min(0); pts = pts - mn + 3
    W, H = int((pts[:,0].max()+3)*T.PPM_S), int((pts[:,1].max()+3)*T.PPM_S)
    img = np.zeros((H, W, 4), np.uint8)
    poly = (pts*T.PPM_S).astype(np.int32)
    cv2.fillPoly(img, [poly], (28, 28, 34, 255))
    inner = np.zeros((H, W), np.uint8); cv2.fillPoly(inner, [poly], 255); inner = cv2.erode(inner, np.ones((int(3*T.PPM_S),)*2, np.uint8))
    img[inner>0, :3] = (30, 100, 170)
    top = pts[pts[:,1].argmin()]
    hc = (int((pts[:,0].mean()-4)*T.PPM_S), int((top[1]+7)*T.PPM_S))
    cv2.circle(img, hc, int(2.0*T.PPM_S), (0,0,0,0), -1)
    truth = (pts[:,0].max()-pts[:,0].min(), pts[:,1].max()-pts[:,1].min())
    area_mm2 = cv2.contourArea(pts)
    return img, truth, area_mm2

def run(label, card, truth, layout="a4", angle=0.0, **cam):
    sheet = T.paste(T.render_sheet(layout), card, T.CENTER[layout], angle)
    a = core.analyze(T.photograph(sheet, **cam))
    holes = [(round(h['d_mm'],1), 'rotura' if h['notch'] else 'redondo', round(h['cy']/10,1)) for h in a.holes]
    print(f"{label:<34} modo={a.seg.mode:<6} medida {a.width_mm:6.2f} x {a.height_mm:6.2f} (verdad {truth[0]:.1f} x {truth[1]:.1f}) | orificios {holes}")
    return a

# 1) tu fallo: letras blancas, un "0" cerca del borde derecho
for flip in (False,):
    c = letters_card(98, 142)
    run("lanyard letras blancas (frente)", c, (98,142), angle=-4, light=0.2)
    run("lanyard letras blancas (reverso)", letters_card(98,142)[:, ::-1].copy(), (98,142), angle=5, light=0.2, seed=2)
# 2) bulto en el contorno: la tarjeta real mide 98 x 142 aunque el bulto sobresalga
run("lanyard con bulto de 1,6 mm", letters_card(98, 142, bump=True), (98,142), angle=3)
# 3) medalla (forma libre) a 0° y a 12°
for ang in (0.0, 12.0):
    m, truth, area = medal(ang)
    a = run(f"medalla forma libre {ang:.0f}°", m, truth, angle=0.0, seed=3)
    alpha_area = (a.alpha > 127).sum() / (core.PX_MM**2)
    print(f"{'':<34} silueta recortada: {alpha_area:.0f} mm² (polígono real {area:.0f} mm²; envolvente convexa daría ~{cv2.contourArea(cv2.convexHull(np.float32([(10,0),(30,2),(45,8),(56,22),(48,34),(40,42),(36,60),(28,61),(22,48),(20,34),(8,30),(0,18),(3,6)]))):.0f})")
