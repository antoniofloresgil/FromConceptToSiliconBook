import unittest

import check_environment as environment

EXPECTED = {'python': '3.12.3', 'yosys': {'path': '/usr/bin/yosys', 'version': 'Yosys 0.33'}, 'cocotb': '2.0.1'}


class CompareTest(unittest.TestCase):
    def test_equal_versions_pass_whatever_the_path(self):
        observed = {'python': '3.12.3', 'yosys': {'path': '/opt/bin/yosys', 'version': 'Yosys 0.33'}, 'cocotb': '2.0.1'}
        self.assertEqual(environment.compare(observed, EXPECTED), [])

    def test_a_different_version_is_reported_with_both_values(self):
        observed = {'python': '3.12.3', 'yosys': {'version': 'Yosys 0.60'}, 'cocotb': '2.0.1'}
        self.assertEqual(environment.compare(observed, EXPECTED), ['yosys: installed Yosys 0.60, validated Yosys 0.33'])

    def test_a_missing_tool_is_a_failure_not_a_skip(self):
        observed = {'python': '3.12.3', 'yosys': None, 'cocotb': None}
        self.assertEqual(environment.compare(observed, EXPECTED),
                         ['yosys: not installed, validated Yosys 0.33', 'cocotb: not installed, validated 2.0.1'])

    def test_every_validated_tool_is_covered_by_the_runner_report(self):
        expected = environment.json.loads(environment.RECORD.read_text(encoding='utf-8'))['tools']
        reported = set(environment.run.tool_info())
        self.assertEqual(sorted(set(expected) - reported), [])


if __name__ == '__main__':
    unittest.main()
