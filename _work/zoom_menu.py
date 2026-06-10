# -*- coding: utf-8 -*-
from PIL import Image
im = Image.open(r"E:\game\_work\f_title.png")
w, h = im.size
print("size", w, h)
# menu panel is on the left ~ x 0.04..0.40, y 0.40..0.92
crop = im.crop((int(w*0.02), int(h*0.40), int(w*0.42), int(h*0.95)))
crop = crop.resize((crop.width*3, crop.height*3), Image.LANCZOS)
crop.save(r"E:\game\_work\menu_zoom2.png")
print("saved menu_zoom2.png", crop.size)
