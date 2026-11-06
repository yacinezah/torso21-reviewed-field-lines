import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('qa',Path(__file__).resolve().parents[1]/'quality/qa.py')
qa=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class Audit(unittest.TestCase):
    def test_group_macro_not_image_macro(self):
        rows=[dict(group_id='A',primary_delta=1.)]*8+[dict(group_id='B',primary_delta=-1.)]
        s=qa.summarize(rows)
        self.assertEqual(s['estimate'],0.)
        self.assertEqual(s['scored_pairs'],9)
        self.assertEqual(s['scored_groups'],2)
        self.assertEqual(s['ci95'],[-1.,1.])

    def test_sample_deterministic_and_no_duplicate(self):
        rows=[dict(id=f'{i:016x}',group_id=str(i%5),original_ambiguous_pixels=int(i==1),
                   width=100,height=100,line_before=10*i,changed_percent=i%8,original_off_palette_pixels=i%2)
              for i in range(60)]
        geometry={r['id']:dict(tiny_components_le4_before=1) for r in rows}
        a=qa.choose(rows,geometry,n=18)
        self.assertEqual(a,qa.choose(rows[::-1],geometry,n=18))
        self.assertEqual(len({x['id'] for x in a}),18)
        self.assertEqual(len({x['group_id'] for x in a}),5)
        self.assertNotIn('0000000000000001',{x['id'] for x in a})
