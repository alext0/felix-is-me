from tests.test_base import TestBase
from util.csv_util import RowDict


class CsvUtilTestCase(TestBase):
    def test_row_dict_returns_none(self):
        row = RowDict({
            'field_a': None,
            'field_b': 'NULL',
            'field_c': '',
            'field_d': 'Test'
        })

        self.assertEqual(row['field_a'], None)
        self.assertEqual(row.get('field_a'), None)

        self.assertEqual(row['field_b'], None)
        self.assertEqual(row.get('field_b'), None)

        self.assertEqual(row['field_c'], None)
        self.assertEqual(row.get('field_c'), None)

        self.assertEqual(row['field_d'], 'Test')
        self.assertEqual(row.get('field_d'), 'Test')

    def test_row_dict_returns_default(self):
        row = RowDict({
            'field_a': None,
            'field_b': 'NULL',
            'field_c': '',
            'field_d': 'Test'
        })

        self.assertEqual(row.get('field_a', 'Test Default Value'), 'Test Default Value')
        self.assertEqual(row.get('field_b', 'Test Default Value'), 'Test Default Value')
        self.assertEqual(row.get('field_c', 'Test Default Value'), 'Test Default Value')
        self.assertEqual(row.get('field_d', 'Test Default Value'), 'Test')
