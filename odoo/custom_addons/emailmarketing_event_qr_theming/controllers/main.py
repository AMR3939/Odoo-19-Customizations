# -*- coding: utf-8 -*-
import io
import qrcode
from odoo import http
from odoo.http import request

class EventQRController(http.Controller):

    @http.route('/event_qr/generate', type='http', auth='public', methods=['GET'])
    def generate_themed_qr(self, text="Scan Me", fg_color="black", bg_color="white", size=10, **kwargs):
        """
        Generates a themed PNG QR code image.
        :param text: Data to encode in the QR (e.g. event URL or registration code)
        :param fg_color: Foreground hex/name color (default: black)
        :param bg_color: Background hex/name color (default: white)
        :param size: Box size of the QR grid
        """
        # Clean/sanitize input colors to prevent crash from empty/invalid color strings
        fg_color = fg_color or "black"
        bg_color = bg_color or "white"
        
        import re
        hex_color_re = re.compile(r'^[0-9a-fA-F]{3,6}$')
        if not fg_color.startswith('#') and hex_color_re.match(fg_color):
            fg_color = f"#{fg_color}"
        if not bg_color.startswith('#') and hex_color_re.match(bg_color):
            bg_color = f"#{bg_color}"
        # If event_id is provided, construct the full event details block
        event_id = kwargs.get('event_id')
        if event_id:
            try:
                event = request.env['event.event'].sudo().browse(int(event_id))
                if event.exists():
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'http://localhost:8069'
                    base_url = base_url.rstrip('/')
                    event_url = f"{base_url}/event/{event.id}"
                    
                    from odoo.fields import Datetime
                    start_str = ""
                    if event.date_begin:
                        start_time = Datetime.context_timestamp(event, event.date_begin)
                        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

                    end_str = ""
                    if event.date_end:
                        end_time = Datetime.context_timestamp(event, event.date_end)
                        end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

                    display_link = event.qr_text or event_url

                    text = (
                        f"Event ID: {event.id}\n"
                        f"Event Name: {event.name or ''}\n"
                        f"Start Date & Time: {start_str}\n"
                        f"End Date & Time: {end_str}\n"
                        f"Event Link: {display_link}"
                    )
            except Exception as e:
                pass

        # New parameters:
        eye_color = kwargs.get('eye_color') or fg_color
        eye_outer_color = kwargs.get('eye_outer_color') or fg_color

        import re
        hex_color_re = re.compile(r'^[0-9a-fA-F]{3,6}$')
        if not fg_color.startswith('#') and hex_color_re.match(fg_color):
            fg_color = f"#{fg_color}"
        if not bg_color.startswith('#') and hex_color_re.match(bg_color):
            bg_color = f"#{bg_color}"
        if not eye_color.startswith('#') and hex_color_re.match(eye_color):
            eye_color = f"#{eye_color}"
        if not eye_outer_color.startswith('#') and hex_color_re.match(eye_outer_color):
            eye_outer_color = f"#{eye_outer_color}"

        border = 2
        # Set up QR code parameters
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=int(size),
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        # We construct the image block-by-block using PIL to support custom eye colors
        from PIL import Image, ImageDraw
        box_size = int(size)
        img_width = (qr.modules_count + 2 * border) * box_size
        img = Image.new("RGBA", (img_width, img_width), bg_color)
        draw = ImageDraw.Draw(img)

        for r in range(qr.modules_count):
            for c in range(qr.modules_count):
                if qr.modules[r][c]:
                    # Determine color for this block
                    color = fg_color
                    is_eye = False
                    
                    # Top-left eye (0..6, 0..6)
                    if 0 <= r < 7 and 0 <= c < 7:
                        is_eye = True
                        dr, dc = r, c
                    # Top-right eye (0..6, N-7..N-1)
                    elif 0 <= r < 7 and (qr.modules_count - 7) <= c < qr.modules_count:
                        is_eye = True
                        dr, dc = r, c - (qr.modules_count - 7)
                    # Bottom-left eye (N-7..N-1, 0..6)
                    elif (qr.modules_count - 7) <= r < qr.modules_count and 0 <= c < 7:
                        is_eye = True
                        dr, dc = r - (qr.modules_count - 7), c
                    
                    if is_eye:
                        if 2 <= dr <= 4 and 2 <= dc <= 4:
                            color = eye_color
                        else:
                            color = eye_outer_color
                    
                    # Draw block
                    x0 = (c + border) * box_size
                    y0 = (r + border) * box_size
                    x1 = x0 + box_size
                    y1 = y0 + box_size
                    draw.rectangle([x0, y0, x1, y1], fill=color)

        # Save image to buffer and return as response
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_image = buffer.getvalue()
        
        return request.make_response(
            qr_image,
            headers=[
                ('Content-Type', 'image/png'),
                ('Content-Length', str(len(qr_image))),
                ('Cache-Control', 'public, max-age=604800')
            ]
        )
