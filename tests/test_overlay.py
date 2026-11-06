import io
from pathlib import Path
import tempfile
import unittest
import zipfile
import numpy as np
from PIL import Image
from torso_line_corrections.core import mask, sha, checked, safe, load_pair
from torso_line_corrections.geometry import measure
from torso_line_corrections.source import extract


def png(a):
    b=io.BytesIO()
    Image.fromarray(a).save(b,format='PNG')
    return b.getvalue()


class Contract(unittest.TestCase):
    def test_upstream_palette_and_unresolved_low_shades(self):
        raw=np.array([[0,16,127,128,254,255]],np.uint8)
        expected=np.array([[0,126,127,255,255,255]],np.uint8)
        np.testing.assert_equal(mask(png(np.stack([raw]*3,axis=-1)),source=True),expected)
        with self.assertRaises(ValueError):
            mask(png(raw))

    def test_bad_png_and_colored_mask(self):
        with self.assertRaises(OSError):
            mask(b'corrupt')
        with self.assertRaises(ValueError):
            mask(png(np.array([[[0,127,255]]],np.uint8)),source=True)

    def test_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as t:
            for p in ('../x','/tmp/x','a//b','a\\b','train/a:b','./x',''):
                with self.subTest(p=p), self.assertRaises(ValueError):
                    safe(t,p)

    def test_tampering_and_changed_count(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'torso';release=root/'release'
            src.mkdir();release.mkdir()
            im=png(np.zeros((6,6,3),np.uint8))
            old=png(np.full((6,6),254,np.uint8))
            v=np.full((6,6),255,np.uint8);v[3,2:5]=127
            revised=png(v)
            (src/'image.png').write_bytes(im);(src/'old.png').write_bytes(old);(release/'new.png').write_bytes(revised)
            r=dict(original_image_path='image.png',original_mask_path='old.png',corrected_mask_path='new.png',
                   original_image_sha256=sha(im),original_mask_sha256=sha(old),corrected_mask_sha256=sha(revised),
                   width=6,height=6,id='sample',original_ambiguous_pixels=0,changed_pixels=3)
            _,before,after=load_pair(release,src,r)
            self.assertTrue((before==255).all())
            self.assertEqual(int((after==127).sum()),3)
            with self.assertRaisesRegex(ValueError,'changed pixel count'):
                load_pair(release,src,dict(r,changed_pixels=4))
            (src/'image.png').write_bytes(im+b'ignored trailer')
            with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
                load_pair(release,src,r)

    def test_zip_alias_uses_safe_extraction_name(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            train=root/'train.zip';test=root/'test.zip';out=root/'local'
            r={}
            with zipfile.ZipFile(train,'w') as z:
                for name,ext in [('image','jpg'),('mask','png')]:
                    b=name.encode()
                    member=f'train/{name}/robot 12:23:34.{ext}'
                    r[f'upstream_{name}_member']=member
                    r[f'original_{name}_path']=member.replace(':','_')
                    r[f'original_{name}_bytes']=len(b)
                    r[f'original_{name}_sha256']=sha(b)
                    z.writestr(member,b)
                z.writestr('../private','ignored')
            with zipfile.ZipFile(test,'w'):
                pass
            extract([r],train,test,out)
            self.assertEqual(checked(out/r['original_mask_path'],sha(b'mask')),b'mask')
            self.assertFalse((root/'private').exists())


class Geometry(unittest.TestCase):
    def test_exact_and_one_pixel_translation(self):
        a=np.zeros((64,64),np.uint8)
        a[8,6:50]=127
        b=np.roll(a,1,axis=0)
        result=measure(a,b)
        self.assertEqual(result['line_dice'],0)
        self.assertEqual(result['centerline_f1_at1px'],1)
        self.assertEqual(result['line_boundary_hd95_px'],1)
        self.assertEqual(result['tangent_histogram_tv'],0)
        self.assertEqual(result['skeleton_length_px_before'],43)
        self.assertEqual(result['width_p50_px_before'],1)
        self.assertEqual(measure(a,a)['cldice'],1)

    def test_empty_cases_not_perfect_scores(self):
        a=np.zeros((12,12),np.uint8); b=a.copy();b[3,3]=127
        self.assertIsNone(measure(a,a)['line_dice'])
        self.assertIsNone(measure(a,b)['line_boundary_mean_px'])
        self.assertEqual(measure(a,b)['centerline_f1_at3px'],0)
        self.assertEqual(measure(a,b)['cldice'],0)

    def test_edge_and_diagonal_geometry(self):
        a=np.zeros((16,16),np.uint8);np.fill_diagonal(a,127)
        r=measure(a,a)
        self.assertAlmostEqual(r['skeleton_length_px_before'],15*np.sqrt(2))
        self.assertEqual(r['components_before'],1)


if __name__=='__main__':
    unittest.main()
