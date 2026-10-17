"""Check catalogue coverage and label insertion without touching RTL listings."""
import copy
import json
import re
import unittest

import learning_paths as paths

class LearningPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(paths.CATALOGUE.read_text(encoding='utf-8'))

    def test_complete_catalogue_and_idempotent_render(self):
        paths.validate(self.data)
        for page in {e['page'] for e in self.data['activities']}:
            text=(paths.ROOT/page).read_text(encoding='utf-8')
            entries=[e for e in self.data['activities'] if e['page']==page]
            rendered=paths.render(text,entries,page)
            self.assertEqual(paths.render(rendered,entries,page),rendered,page)
            self.assertEqual(re.findall(r'^```[^\n]*\n.*?^```',text,re.M|re.S),
                             re.findall(r'^```[^\n]*\n.*?^```',rendered,re.M|re.S),page)

    def test_nested_questions_and_code_are_not_extra_experiments(self):
        text='''## Hands-on Experiments

### Experiment 1: a block
1. A substep of this experiment.
```text
### Experiment 2: not a real heading
1. not an exercise
```
### Reviewing an integration
1. A review question.
## Key ideas
'''
        self.assertEqual(paths.discover(text),[('heading','### Experiment 1: a block','hands')])

    def test_missing_activity_and_duplicate_id_fail(self):
        data=copy.deepcopy(self.data)
        i=next(i for i,e in enumerate(data['activities']) if e['group']=='hands')
        data['activities'].pop(i)
        with self.assertRaisesRegex(ValueError,'coverage drift'):paths.validate(data)
        data=copy.deepcopy(self.data);data['activities'].append(data['activities'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate'):paths.validate(data)

    def test_invalid_cost_and_unscoped_core_fail(self):
        data=copy.deepcopy(self.data);data['activities'][0]['cost']='fast enough'
        with self.assertRaisesRegex(ValueError,'compute class'):paths.validate(data)
        data=copy.deepcopy(self.data);data['activities'][0].update(role='core',practice='')
        with self.assertRaisesRegex(ValueError,'milestone'):paths.validate(data)

    def test_explicit_reference_run_is_not_a_report_only_review(self):
        data=copy.deepcopy(self.data)
        entry=next(e for e in data['activities'] if e['id']=='cocotb-review')
        entry['cost']='C0'
        with self.assertRaisesRegex(ValueError,'Executable review cannot be C0'):paths.validate(data)

if __name__=='__main__':unittest.main()
