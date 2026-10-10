"""Bounded pixel adjustments; preserves original alpha and dimensions."""
import io
import random
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from PySide6.QtGui import QImage

# label: parameter label, default, minimum, maximum, decimal places
EFFECTS = {
 'Luminosité':('Facteur',1,0,5,2), 'Contraste':('Facteur',1,0,5,2),
 'Saturation':('Facteur',1,0,5,2), 'Exposition':('Diaphragmes',0,-5,5,2),
 'Gamma / courbe tonale':('Gamma',1,.1,5,2), 'Niveaux automatiques':None,
 'Teinte':('Rotation en degrés',0,-180,180,0),
 'Température':('Chaud / froid',0,-100,100,0),
 'Noir et blanc':None, 'Inverser les couleurs':None,
 'Seuil':('Seuil',128,0,255,0), 'Isohélie':('Nombre de bits',4,1,8,0),
 'Flou gaussien':('Rayon en pixels',2,0,30,1),
 'Flou médian':('Diamètre impair en pixels',3,3,15,0),
 'Accentuation':('Intensité en %',150,0,500,0),
 'Netteté':('Facteur',1,0,5,2), 'Détection des contours':None,
 'Relief':None, 'Pixellisation':('Taille des blocs en pixels',8,1,100,0),
 'Bruit':('Intensité',10,0,100,0),
}

def render_effect(image,kind,value=1):
 from model import png_bytes
 source=Image.open(io.BytesIO(png_bytes(image))).convert('RGBA');alpha=source.getchannel('A');rgb=source.convert('RGB')
 if kind in ('Luminosité','Contraste','Saturation','Netteté'):
  cls={'Luminosité':ImageEnhance.Brightness,'Contraste':ImageEnhance.Contrast,'Saturation':ImageEnhance.Color,'Netteté':ImageEnhance.Sharpness}[kind];rgb=cls(rgb).enhance(value)
 elif kind=='Exposition':rgb=rgb.point([min(255,round(i*2**value)) for i in range(256)]*3)
 elif kind=='Gamma / courbe tonale':rgb=rgb.point([round(255*(i/255)**(1/value)) for i in range(256)]*3)
 elif kind=='Niveaux automatiques':rgb=ImageOps.autocontrast(rgb,ignore=0)
 elif kind=='Teinte':
  h,s,v=rgb.convert('HSV').split();h=h.point([(i+round(value/360*255))%256 for i in range(256)]);rgb=Image.merge('HSV',(h,s,v)).convert('RGB')
 elif kind=='Température':
  r,g,b=rgb.split();delta=round(value*.8);r=r.point([max(0,min(255,i+delta)) for i in range(256)]);b=b.point([max(0,min(255,i-delta)) for i in range(256)]);rgb=Image.merge('RGB',(r,g,b))
 elif kind=='Noir et blanc':rgb=ImageOps.grayscale(rgb).convert('RGB')
 elif kind=='Inverser les couleurs':rgb=ImageOps.invert(rgb)
 elif kind=='Seuil':rgb=ImageOps.grayscale(rgb).point([255 if i>=value else 0 for i in range(256)]).convert('RGB')
 elif kind=='Isohélie':rgb=ImageOps.posterize(rgb,max(1,min(8,round(value))))
 elif kind in ('Flou','Flou gaussien'):rgb=rgb.filter(ImageFilter.GaussianBlur(value))
 elif kind=='Flou médian':rgb=rgb.filter(ImageFilter.MedianFilter(max(3,round(value)//2*2+1)))
 elif kind=='Accentuation':rgb=rgb.filter(ImageFilter.UnsharpMask(radius=2,percent=round(value),threshold=3))
 elif kind=='Détection des contours':rgb=rgb.filter(ImageFilter.FIND_EDGES)
 elif kind=='Relief':rgb=rgb.filter(ImageFilter.EMBOSS)
 elif kind=='Pixellisation':
  block=max(1,round(value));rgb=rgb.resize((max(1,rgb.width//block),max(1,rgb.height//block)),Image.Resampling.BOX).resize(rgb.size,Image.Resampling.NEAREST)
 elif kind=='Bruit':
  rng=random.Random(42);noise=Image.frombytes('L',rgb.size,bytes(max(0,min(255,round(128+rng.gauss(0,value)))) for _ in range(rgb.width*rgb.height)))
  from PIL import ImageChops
  rgb=ImageChops.add(rgb,Image.merge('RGB',(noise,noise,noise)),offset=-128)
 else:raise ValueError('Effet inconnu : '+kind)
 rgb.putalpha(alpha);data=rgb.tobytes();return QImage(data,rgb.width,rgb.height,QImage.Format_RGBA8888).copy().convertToFormat(QImage.Format_ARGB32_Premultiplied)
