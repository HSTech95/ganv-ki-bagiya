import io
import os
import base64
import qrcode
from urllib.parse import quote_plus
from django.conf import settings


def generate_upi_payload(upi_id="8937877789@ybl", merchant_name="JAVED ALI", amount=None, donation_id=None):
    """
    Constructs NPCI compliant PhonePe / UPI deep-link URL.
    Format: upi://pay?pa=8937877789@ybl&pn=JAVED%20ALI&mc=0000&mode=02&purpose=00&am=...&cu=INR&tn=...
    """
    name_encoded = quote_plus(str(merchant_name or "JAVED ALI"))
    params = [
        f"pa={upi_id or '8937877789@ybl'}",
        f"pn={name_encoded}",
        "mc=0000",
        "mode=02",
        "purpose=00",
    ]
    if amount:
        params.append(f"am={float(amount):.2f}")
    params.append("cu=INR")
    if donation_id:
        note_encoded = quote_plus(f"Bagiya Donation {donation_id}")
        params.append(f"tn={note_encoded}")
    return "upi://pay?" + "&".join(params)


def get_phonepe_qr_base64():
    """
    Loads and returns base64 PNG data URI for the official PhonePe QR code.
    """
    possible_paths = [
        os.path.join(settings.BASE_DIR, "static", "images", "phonepe_qr.png"),
        os.path.join(settings.BASE_DIR, "static", "images", "phonepe_qr.jpg"),
        os.path.join(settings.BASE_DIR, "media", "qr_codes", "phonepe_qr.png"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            ext = "png" if p.endswith(".png") else "jpeg"
            with open(p, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{ext};base64,{b64_str}"
    return None


def generate_upi_qr_base64(payload=None):
    """
    Returns the official PhonePe QR code if available, otherwise generates
    a high-quality base64 PNG data URI from the payload.
    """
    phonepe_qr = get_phonepe_qr_base64()
    if phonepe_qr:
        return phonepe_qr

    if not payload:
        payload = "upi://pay?pa=8937877789@ybl&pn=JAVED%20ALI&mc=0000&mode=02&purpose=00"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f5132", back_color="#ffffff")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
