import streamlit as st
import anthropic
import os
import tempfile
import zipfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import base64

st.set_page_config(
    page_title="VideoAI Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: #0a0a0f; color: #e8e8f0; }
    .main-title {
        font-size: 2.2rem; font-weight: 700; text-align: center;
        background: linear-gradient(135deg, #7c5cfc, #fc5c7d);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle { text-align: center; color: #6b6b80; font-size: 0.9rem; margin-bottom: 2rem; }
    .section-card {
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;
    }
    .section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: #6b6b80; margin-bottom: 0.8rem; }
    .ai-box {
        background: rgba(124,92,252,0.08); border: 1px solid rgba(124,92,252,0.3);
        border-radius: 10px; padding: 1rem; margin-top: 0.5rem;
        color: rgba(255,255,255,0.85); font-size: 0.9rem; line-height: 1.6;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c5cfc, #fc5c7d) !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button:hover { opacity: 0.88 !important; }
    .result-video { border-radius: 12px; border: 2px solid rgba(124,92,252,0.4); }
    div[data-testid="stFileUploader"] {
        background: rgba(124,92,252,0.05); border: 1.5px dashed rgba(124,92,252,0.4);
        border-radius: 12px; padding: 0.5rem;
    }
    .stSelectbox > div > div { background: #1a1a24 !important; color: #e8e8f0 !important; }
    .stTextArea > div > textarea { background: #1a1a24 !important; color: #e8e8f0 !important; border-color: rgba(124,92,252,0.4) !important; }
    .stSlider > div { color: #e8e8f0; }
    label { color: #b0b0c0 !important; }
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 0.7rem; font-weight: 700;
        background: rgba(124,92,252,0.2); color: #a78bfa;
        border: 1px solid rgba(124,92,252,0.4); margin-right: 4px; margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def get_ai_suggestions(prompt, context):
    if not ANTHROPIC_API_KEY:
        return "⚠️ Chưa có API key. Thêm ANTHROPIC_API_KEY vào Streamlit Secrets để dùng tính năng AI."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Bạn là chuyên gia chỉnh sửa video chuyên nghiệp. 
Context: {context}
Yêu cầu: {prompt}
Hãy đưa ra gợi ý cụ thể, ngắn gọn bằng tiếng Việt về cách tối ưu video này (nhạc, text, hiệu ứng, chuyển cảnh). Tối đa 150 từ."""
            }]
        )
        return message.content[0].text
    except Exception as e:
        return f"Lỗi AI: {str(e)}"

def create_text_frame(width, height, title, subtitle, bg_color, text_color, font_size, effect):
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(font_size//2, 14))
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    if effect == "Gradient":
        arr = np.array(img).astype(float)
        for y in range(height):
            factor = y / height
            arr[y, :, 0] = min(255, arr[y, :, 0] * (1 - factor * 0.3))
            arr[y, :, 2] = min(255, arr[y, :, 2] + factor * 60)
        img = Image.fromarray(arr.astype(np.uint8))
        draw = ImageDraw.Draw(img)

    elif effect == "Vignette":
        arr = np.array(img).astype(float)
        cx, cy = width // 2, height // 2
        Y, X = np.ogrid[:height, :width]
        dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
        max_dist = np.sqrt(cx**2 + cy**2)
        mask = 1 - (dist / max_dist) * 0.7
        for c in range(3):
            arr[:, :, c] = arr[:, :, c] * mask
        img = Image.fromarray(arr.astype(np.uint8))
        draw = ImageDraw.Draw(img)

    if title:
        try:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except:
            tw, th = draw.textsize(title, font=font_title)
        tx = (width - tw) // 2
        ty = (height - th) // 2 - 20
        if effect == "Shadow":
            draw.text((tx + 3, ty + 3), title, fill=(0, 0, 0), font=font_title)
        draw.text((tx, ty), title, fill=text_color, font=font_title)

    if subtitle:
        try:
            bbox2 = draw.textbbox((0, 0), subtitle, font=font_sub)
            sw = bbox2[2] - bbox2[0]
        except:
            sw, _ = draw.textsize(subtitle, font=font_sub)
        sx = (width - sw) // 2
        sy = ty + th + 15 if title else height // 2
        draw.text((sx, sy), subtitle, fill=(*text_color[:3], 180) if len(text_color) == 4 else text_color, font=font_sub)

    return img

def make_slideshow_frames(images, titles, subtitles, settings):
    frames = []
    w, h = settings["size"]
    fps = settings["fps"]
    dur = settings["clip_duration"]
    trans_dur = settings["transition_duration"]
    font_size = settings["font_size"]
    bg_color = settings["bg_color"]
    text_color = settings["text_color"]
    effect = settings["effect"]

    frames_per_clip = int(fps * dur)
    frames_per_trans = int(fps * trans_dur)

    for i, img in enumerate(images):
        pil_img = img.resize((w, h), Image.LANCZOS)
        title = titles[i] if i < len(titles) else ""
        sub = subtitles[i] if i < len(subtitles) else ""

        text_frame = create_text_frame(w, h, title, sub, bg_color, text_color, font_size, effect)
        blended = Image.blend(pil_img.convert("RGBA"), text_frame.convert("RGBA"), alpha=0.55).convert("RGB")

        for _ in range(frames_per_clip):
            frames.append(np.array(blended))

        if i < len(images) - 1:
            next_img = images[i + 1].resize((w, h), Image.LANCZOS)
            next_text = create_text_frame(w, h, titles[i+1] if i+1 < len(titles) else "",
                                          subtitles[i+1] if i+1 < len(subtitles) else "",
                                          bg_color, text_color, font_size, effect)
            next_blended = Image.blend(next_img.convert("RGBA"), next_text.convert("RGBA"), alpha=0.55).convert("RGB")

            trans = settings["transition"]
            for t in range(frames_per_trans):
                alpha = t / frames_per_trans
                if trans == "Fade":
                    frame = Image.blend(blended, next_blended, alpha=alpha)
                    frames.append(np.array(frame))
                elif trans == "Slide phải → trái":
                    offset = int(alpha * w)
                    frame = Image.new("RGB", (w, h))
                    frame.paste(blended.crop((offset, 0, w, h)), (0, 0))
                    frame.paste(next_blended.crop((0, 0, w - offset, h)), (w - offset, 0))
                    frames.append(np.array(frame))
                elif trans == "Zoom In":
                    scale = 1 + alpha * 0.3
                    nw, nh = int(w * scale), int(h * scale)
                    zoomed = blended.resize((nw, nh), Image.LANCZOS)
                    x, y = (nw - w) // 2, (nh - h) // 2
                    frame = zoomed.crop((x, y, x + w, y + h))
                    frame = Image.blend(frame, next_blended, alpha=alpha)
                    frames.append(np.array(frame))
                else:
                    frame = Image.blend(blended, next_blended, alpha=alpha)
                    frames.append(np.array(frame))
    return frames

def export_gif(frames, fps):
    pil_frames = [Image.fromarray(f) for f in frames[::3]]
    buf = io.BytesIO()
    pil_frames[0].save(buf, format="GIF", save_all=True,
                       append_images=pil_frames[1:],
                       duration=int(1000 / fps * 3), loop=0)
    return buf.getvalue()

# ─── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">✦ VideoAI Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tạo video chuyên nghiệp với AI • Hỗ trợ mọi kích thước • Xuất GIF & Video</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.6], gap="large")

with col_left:
    st.markdown('<div class="section-title">📁 Tải ảnh / video lên</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Chọn ảnh (JPG, PNG) hoặc nhiều ảnh",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    st.markdown('<div class="section-title" style="margin-top:1rem">📐 Kích thước</div>', unsafe_allow_html=True)
    size_opt = st.selectbox("", ["16:9 — YouTube / Landscape (1280×720)",
                                  "9:16 — TikTok / Reels (720×1280)",
                                  "1:1 — Instagram Square (720×720)",
                                  "4:5 — Instagram Portrait (720×900)"],
                             label_visibility="collapsed")
    size_map = {
        "16:9 — YouTube / Landscape (1280×720)": (1280, 720),
        "9:16 — TikTok / Reels (720×1280)": (720, 1280),
        "1:1 — Instagram Square (720×720)": (720, 720),
        "4:5 — Instagram Portrait (720×900)": (720, 900),
    }
    out_size = size_map[size_opt]

    st.markdown('<div class="section-title" style="margin-top:1rem">🎬 Chuyển cảnh</div>', unsafe_allow_html=True)
    transition = st.selectbox("", ["Fade", "Slide phải → trái", "Zoom In"], label_visibility="collapsed")

    st.markdown('<div class="section-title" style="margin-top:1rem">✨ Hiệu ứng hình ảnh</div>', unsafe_allow_html=True)
    effect = st.selectbox("", ["Không có", "Gradient", "Vignette", "Shadow"], label_visibility="collapsed")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">🎨 Màu nền</div>', unsafe_allow_html=True)
        bg_hex = st.color_picker("", "#1a1a2e", label_visibility="collapsed")
    with c2:
        st.markdown('<div class="section-title">🔤 Màu chữ</div>', unsafe_allow_html=True)
        txt_hex = st.color_picker("", "#ffffff", label_visibility="collapsed")

    font_size = st.slider("Cỡ chữ tiêu đề", 18, 72, 36)

    c3, c4 = st.columns(2)
    with c3:
        clip_dur = st.slider("Thời lượng mỗi ảnh (giây)", 1, 10, 3)
    with c4:
        trans_dur = st.slider("Chuyển cảnh (giây)", 1, 3, 1)

    st.markdown('<div class="section-title" style="margin-top:1rem">🎵 Nhạc nền</div>', unsafe_allow_html=True)
    music_style = st.selectbox("", ["Upbeat 🔥", "Chill 🌊", "Dramatic 🎭", "Lo-fi 🎧", "Không có"], label_visibility="collapsed")

with col_right:
    st.markdown('<div class="section-title">📝 Text cho từng ảnh</div>', unsafe_allow_html=True)

    titles, subtitles = [], []

    if uploaded:
        for i, f in enumerate(uploaded):
            with st.expander(f"Ảnh {i+1}: {f.name}", expanded=(i == 0)):
                t = st.text_input(f"Tiêu đề ảnh {i+1}", value=f"Cảnh {i+1}", key=f"title_{i}")
                s = st.text_input(f"Phụ đề ảnh {i+1}", value="", key=f"sub_{i}", placeholder="Caption, hashtag...")
                titles.append(t)
                subtitles.append(s)
    else:
        st.info("⬅️ Tải ảnh lên để bắt đầu chỉnh sửa text cho từng cảnh.")

    st.markdown("---")
    st.markdown('<div class="section-title">🤖 Gợi ý AI (tuỳ chọn)</div>', unsafe_allow_html=True)

    sugg_cols = st.columns(2)
    suggestions = ["Làm video viral TikTok", "Video sản phẩm chuyên nghiệp",
                   "Kể chuyện cảm xúc", "Quảng cáo bắt mắt"]
    for i, s in enumerate(suggestions):
        if sugg_cols[i % 2].button(s, key=f"sugg_{i}"):
            st.session_state["ai_prompt"] = s

    ai_prompt = st.text_area("Mô tả yêu cầu chỉnh sửa của bạn...",
                              value=st.session_state.get("ai_prompt", ""),
                              height=80, placeholder="VD: Làm video TikTok năng động, thêm text bắt mắt...")

    if st.button("✨ Hỏi AI gợi ý"):
        if ai_prompt:
            context = f"Video có {len(uploaded) if uploaded else 0} ảnh, kích thước {size_opt}, nhạc {music_style}, chuyển cảnh {transition}"
            with st.spinner("AI đang phân tích..."):
                result = get_ai_suggestions(ai_prompt, context)
            st.markdown(f'<div class="ai-box">🤖 {result}</div>', unsafe_allow_html=True)
        else:
            st.warning("Nhập yêu cầu trước nhé!")

st.markdown("---")

col_gen, col_dl = st.columns([2, 1])
with col_gen:
    generate = st.button("🎬 Tạo Video / GIF ngay!", use_container_width=True)

if generate:
    if not uploaded:
        st.error("Vui lòng tải lên ít nhất 1 ảnh!")
    else:
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        settings = {
            "size": out_size,
            "fps": 24,
            "clip_duration": clip_dur,
            "transition_duration": trans_dur,
            "transition": transition,
            "effect": effect,
            "font_size": font_size,
            "bg_color": hex_to_rgb(bg_hex),
            "text_color": hex_to_rgb(txt_hex),
        }

        images = [Image.open(f).convert("RGB") for f in uploaded]

        with st.spinner("⚙️ Đang tạo video..."):
            frames = make_slideshow_frames(images, titles, subtitles, settings)
            gif_bytes = export_gif(frames, settings["fps"])

        st.success(f"✅ Xong! {len(frames)} frames — {len(uploaded)} cảnh — {transition}")

        preview_size = (480, int(480 * out_size[1] / out_size[0]))
        st.markdown("**Xem trước:**")
        st.image(gif_bytes, use_column_width=False, width=min(480, out_size[0]))

        st.download_button(
            label="⬇️ Tải GIF về máy",
            data=gif_bytes,
            file_name="videoai_studio.gif",
            mime="image/gif",
            use_container_width=True
        )

        st.info("💡 Tip: GIF này có thể đăng thẳng lên TikTok, Instagram, Zalo! Để xuất MP4 chất lượng cao, bạn cần thêm thư viện moviepy (có thể nâng cấp sau).")
