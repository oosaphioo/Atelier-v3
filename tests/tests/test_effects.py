import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from PySide6.QtGui import QColor
from model import Project,MODES,blank
from effects import EFFECTS

class EffectTests(unittest.TestCase):
 def test_all_effects_preserve_alpha_mask_and_undo(self):
  for name,spec in EFFECTS.items():
   with self.subTest(name=name):
    p=Project(9,9)
    for y in range(9):
     for x in range(9):p.layer.image.setPixelColor(x,y,QColor(20+x*20,30+y*20,80,(x+y)*15))
    p.add_mask();original=p.layer.image.copy();mask=p.layer.mask.copy();n=len(p.undo_stack)
    p.adjust(name,spec[1] if spec else 1)
    self.assertEqual(p.layer.image.size(),original.size());self.assertEqual(p.layer.mask,mask);self.assertEqual(len(p.undo_stack),n+1)
    for y in range(9):
     for x in range(9):self.assertEqual(p.layer.image.pixelColor(x,y).alpha(),original.pixelColor(x,y).alpha())
    p.undo();self.assertEqual(p.layer.image,original)
 def test_locked_and_invalid_do_not_mutate(self):
  p=Project(5,5);p.layer.locked=True
  with self.assertRaises(ValueError):p.adjust('Seuil',100)
  self.assertEqual(len(p.undo_stack),0);p.layer.locked=False
  with self.assertRaises(ValueError):p.adjust('Unknown')
  self.assertEqual(len(p.undo_stack),0)
 def test_blend_modes_roundtrip_and_expected_pixels(self):
  p=Project(3,3);p.layer.image.fill(QColor(80,100,120));p.add('Top');p.layer.image.fill(QColor(160,140,120))
  with tempfile.TemporaryDirectory() as tmp:
   for mode in MODES:
    p.layer.mode=mode;p.invalidate();image=p.composite();self.assertEqual(image.pixelColor(0,0).alpha(),255)
    path=Path(tmp)/'blend.atelier';p.save(path);q=Project.load(path);self.assertEqual(q.layer.mode,mode);self.assertEqual(q.composite(),image)
  p.layer.mode='Produit';p.invalidate();self.assertAlmostEqual(p.composite().pixelColor(0,0).red(),50,delta=1)
  p.layer.mode='Différence';p.invalidate();self.assertAlmostEqual(p.composite().pixelColor(0,0).red(),80,delta=1)
 def test_preview_cancel_and_accept(self):
  from PySide6.QtWidgets import QApplication,QDialog
  from PySide6.QtCore import QTimer,QStandardPaths
  from main import Window
  app=QApplication.instance() or QApplication([]);QStandardPaths.setTestModeEnabled(True)
  w=Window();w.timer.stop();w.project=Project(5,5);w.project.layer.image.fill(QColor(100,50,20,128));original=w.project.layer.image.copy()
  def close_dialog(accept):
   for widget in app.topLevelWidgets():
    if isinstance(widget,QDialog):widget.accept() if accept else widget.reject()
  QTimer.singleShot(0,lambda:close_dialog(False));w.effect_dialog('Inverser les couleurs');self.assertEqual(w.project.layer.image,original);self.assertEqual(len(w.project.undo_stack),0)
  QTimer.singleShot(0,lambda:close_dialog(True));w.effect_dialog('Inverser les couleurs');self.assertEqual(len(w.project.undo_stack),1);self.assertTrue(w.dirty);self.assertGreater(w.project.layer.image.pixelColor(0,0).red(),140)
  w.project.undo();self.assertEqual(w.project.layer.image,original);w.deleteLater()
