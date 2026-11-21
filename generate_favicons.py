from PIL import Image, ImageDraw
import math

def generate_master_icon(dim=512):
    S = 2
    W = dim * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient background squircle
    radius = int(W * 0.23)
    mask = Image.new("L", (W, W), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, W - 1, W - 1], radius=radius, fill=255)

    # Teal gradient image
    grad_img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad_img)
    for y in range(W):
        t = y / float(W)
        r = int(4 + t * (20 - 4))
        g = int(47 + t * (184 - 47))
        b = int(46 + t * (166 - 46))
        grad_draw.line([(0, y), (W, y)], fill=(r, g, b, 255))
    
    img.paste(grad_img, (0, 0), mask)

    # Subtle inner border
    inner_mask = Image.new("L", (W, W), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    border_inset = int(6 * S)
    inner_draw.rounded_rectangle([border_inset, border_inset, W - 1 - border_inset, W - 1 - border_inset], 
                                radius=radius - border_inset, outline=255, width=int(2.5 * S))
    border_img = Image.new("RGBA", (W, W), (255, 255, 255, 45))
    img.paste(border_img, (0, 0), inner_mask)

    # Globe center & radius
    cx = int(236 * S)
    cy = int(272 * S)
    r = int(132 * S)

    # Globe body
    globe_mask = Image.new("L", (W, W), 0)
    g_draw = ImageDraw.Draw(globe_mask)
    g_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    globe_img = Image.new("RGBA", (W, W), (6, 55, 53, 230))
    img.paste(globe_img, (0, 0), globe_mask)

    # Globe outline
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(94, 234, 212, 255), width=int(6 * S))

    # Globe latitude arcs (equator & parallels)
    draw.ellipse([cx - r, cy - int(46 * S), cx + r, cy + int(46 * S)], outline=(45, 212, 191, 175), width=int(4 * S))
    draw.ellipse([cx - int(114 * S), cy - int(56 * S) - int(34 * S), cx + int(114 * S), cy - int(56 * S) + int(34 * S)], 
                 outline=(45, 212, 191, 120), width=int(3 * S))
    draw.ellipse([cx - int(114 * S), cy + int(56 * S) - int(34 * S), cx + int(114 * S), cy + int(56 * S) + int(34 * S)], 
                 outline=(45, 212, 191, 120), width=int(3 * S))

    # Globe meridian
    draw.ellipse([cx - int(58 * S), cy - r, cx + int(58 * S), cy + r], outline=(45, 212, 191, 175), width=int(4 * S))
    draw.line([(cx, cy - r), (cx, cy + r)], fill=(45, 212, 191, 160), width=int(3.5 * S))

    # Orbiting flight path (dashed swooping arc)
    trail_points = []
    p0 = (102 * S, 344 * S)
    p1 = (120 * S, 440 * S)
    p2 = (340 * S, 430 * S)
    p3 = (380 * S, 180 * S)

    for i in range(100):
        t = i / 100.0
        bx = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
        by = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
        trail_points.append((bx, by))

    for idx in range(len(trail_points) - 1):
        if (idx // 3) % 2 == 0:
            pt1 = trail_points[idx]
            pt2 = trail_points[idx + 1]
            alpha = int(40 + (idx / float(len(trail_points))) * 215)
            draw.line([pt1, pt2], fill=(255, 255, 255, alpha), width=int(6 * S))

    # Supersonic Airplane
    plane_cx = 378 * S
    plane_cy = 142 * S
    angle_rad = math.radians(42)

    raw_points = [
        (0, -48), (4, -30), (7, 0), (52, 20), (52, 30),
        (7, 16), (7, 36), (22, 48), (22, 56), (0, 50),
        (-22, 56), (-22, 48), (-7, 36), (-7, 16), (-52, 30),
        (-52, 20), (-7, 0), (-4, -30)
    ]

    transformed_points = []
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    for px, py in raw_points:
        sx = px * S
        sy = py * S
        rx = sx * cos_a - sy * sin_a + plane_cx
        ry = sx * sin_a + sy * cos_a + plane_cy
        transformed_points.append((rx, ry))

    # Drop shadow
    shadow_points = [(x + 4 * S, y + 8 * S) for x, y in transformed_points]
    draw.polygon(shadow_points, fill=(2, 28, 26, 120))

    # Plane fill
    draw.polygon(transformed_points, fill=(255, 255, 255, 255))

    # Cockpit detail
    cockpit_raw = [(0, -36), (2, -18), (-2, -18)]
    cockpit_tf = [
        (px * S * cos_a - py * S * sin_a + plane_cx,
         px * S * sin_a + py * S * cos_a + plane_cy)
        for px, py in cockpit_raw
    ]
    draw.polygon(cockpit_tf, fill=(45, 212, 191, 230))

    # Sparkle star in upper right
    sp_cx = 424 * S
    sp_cy = 88 * S
    sp_r = 18 * S
    sp_points = [
        (sp_cx, sp_cy - sp_r),
        (sp_cx + sp_r * 0.25, sp_cy - sp_r * 0.25),
        (sp_cx + sp_r, sp_cy),
        (sp_cx + sp_r * 0.25, sp_cy + sp_r * 0.25),
        (sp_cx, sp_cy + sp_r),
        (sp_cx - sp_r * 0.25, sp_cy + sp_r * 0.25),
        (sp_cx - sp_r, sp_cy),
        (sp_cx - sp_r * 0.25, sp_cy - sp_r * 0.25),
    ]
    draw.polygon(sp_points, fill=(254, 240, 138, 255))

    # Small sparkle
    sm_cx = 92 * S
    sm_cy = 138 * S
    sm_r = 11 * S
    sm_points = [
        (sm_cx, sm_cy - sm_r),
        (sm_cx + sm_r * 0.25, sm_cy - sm_r * 0.25),
        (sm_cx + sm_r, sm_cy),
        (sm_cx + sm_r * 0.25, sm_cy + sm_r * 0.25),
        (sm_cx, sm_cy + sm_r),
        (sm_cx - sm_r * 0.25, sm_cy + sm_r * 0.25),
        (sm_cx - sm_r, sm_cy),
        (sm_cx - sm_r * 0.25, sm_cy - sm_r * 0.25),
    ]
    draw.polygon(sm_points, fill=(167, 243, 208, 210))

    # Lanczos downsampling to master dim
    return img.resize((dim, dim), Image.Resampling.LANCZOS)

if __name__ == "__main__":
    master = generate_master_icon(512)
    master.save("icon-512.png", "PNG")

    icon_192 = master.resize((192, 192), Image.Resampling.LANCZOS)
    icon_192.save("icon-192.png", "PNG")

    icon_180 = master.resize((180, 180), Image.Resampling.LANCZOS)
    icon_180.save("apple-touch-icon.png", "PNG")

    icon_32 = master.resize((32, 32), Image.Resampling.LANCZOS)
    icon_32.save("favicon.png", "PNG")

    icon_16 = master.resize((16, 16), Image.Resampling.LANCZOS)
    icon_48 = master.resize((48, 48), Image.Resampling.LANCZOS)
    
    # Save multi-size favicon.ico
    icon_48.save("favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[icon_16, icon_32])

    print("All favicon assets generated successfully!")
