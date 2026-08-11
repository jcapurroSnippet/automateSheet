import csv
import io
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from config_rif import RIFConfig as Config
from rif_scheduler import RIFScheduler


class FakeBlob:
    def __init__(self, object_name):
        self.object_name = object_name
        self.uploaded_bytes = b""
        self.content_type = None

    def upload_from_filename(self, filename, content_type=None):
        self.uploaded_bytes = Path(filename).read_bytes()
        self.content_type = content_type


class FakeBucket:
    def __init__(self, name):
        self.name = name
        self.last_blob = None

    def blob(self, object_name):
        self.last_blob = FakeBlob(object_name)
        return self.last_blob


class FakeStorageClient:
    def __init__(self):
        self.last_bucket = None

    def bucket(self, name):
        self.last_bucket = FakeBucket(name)
        return self.last_bucket


class RIFSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = RIFScheduler()

    def build_meta_data(self):
        return [
            ['id', 'title', 'description', 'availability', 'condition', 'price', 'link', 'image_link', 'brand', 'gender', 'age_group', 'gtin', 'additional_image_link'],
            ['EMBARIFV2', 'Executive MBA', 'Original', 'in stock', 'new', '10', 'https://example.com/emba', 'https://img/emba.png', 'UdeSA', 'unisex', 'adult', '', 'https://img/a.png|https://img/b.png'],
            ['MBASRIF', 'MBA Salud', '', 'in stock', 'new', '10', 'https://example.com/mbas', 'https://img/mbas.png', 'UdeSA', 'unisex', 'adult', '', ''],
            ['EMBA', 'Executive MBA', 'Keep', 'in stock', 'new', '10', 'https://example.com/emba-dual', 'https://img/emba-dual.png', 'UdeSA', 'unisex', 'adult', '', ''],
        ]

    def test_build_rif_description_updates_known_rif_ids(self):
        next_10_events = {
            'EMBARIF': '25/03',
            'MBASRIF': False,
        }

        self.assertEqual(
            self.scheduler.build_rif_description('EMBARIFV2', 'Original', next_10_events),
            'Próxima reunión informativa: 25/03'
        )
        self.assertEqual(
            self.scheduler.build_rif_description('MBASRIF', 'Original', next_10_events),
            ''
        )
        self.assertEqual(
            self.scheduler.build_rif_description('EMBA', 'Original', next_10_events),
            'Original'
        )

    def test_build_tiktok_catalog_rows_uses_meta_sheet_data(self):
        rows = self.scheduler.build_tiktok_catalog_rows(self.build_meta_data())

        self.assertEqual(rows[0]['sku_id'], 'EMBARIFV2')
        self.assertEqual(rows[0]['title'], 'Executive MBA')
        self.assertEqual(rows[0]['description'], 'Original')
        self.assertEqual(rows[0]['additional_image_link'], 'https://img/a.png,https://img/b.png')
        self.assertEqual(rows[2]['sku_id'], 'EMBA')
        self.assertEqual(list(rows[0].keys()), list(self.scheduler.TIKTOK_CATALOG_HEADERS))

    def test_export_tiktok_catalog_updates_csv_and_uploads_to_gcs(self):
        fake_client = FakeStorageClient()
        success = self.scheduler.export_tiktok_catalog(
            bucket_name='bucket-test',
            object_name='catalogs/catalog_tiktok.csv',
            storage_client=fake_client,
            meta_data=self.build_meta_data()
        )

        self.assertTrue(success)
        self.assertEqual(fake_client.last_bucket.name, 'bucket-test')
        self.assertEqual(fake_client.last_bucket.last_blob.object_name, 'catalogs/catalog_tiktok.csv')
        self.assertEqual(fake_client.last_bucket.last_blob.content_type, 'text/csv')

        uploaded_text = fake_client.last_bucket.last_blob.uploaded_bytes.decode('utf-8-sig')
        parsed_rows = list(csv.DictReader(io.StringIO(uploaded_text)))

        self.assertEqual(parsed_rows[0]['description'], 'Original')
        self.assertEqual(parsed_rows[1]['description'], '')
        self.assertEqual(parsed_rows[2]['description'], 'Keep')
        self.assertEqual(
            parsed_rows[0]['additional_image_link'],
            'https://img/a.png,https://img/b.png'
        )
        self.assertEqual(
            list(parsed_rows[0].keys()),
            list(self.scheduler.TIKTOK_CATALOG_HEADERS)
        )

    def test_export_tiktok_catalog_fails_when_bucket_is_missing(self):
        with patch.object(Config, 'TIKTOK_CATALOG_BUCKET', ''):
            success = self.scheduler.export_tiktok_catalog(
                bucket_name='',
                meta_data=self.build_meta_data()
            )

        self.assertFalse(success)
        self.assertTrue(
            any('TIKTOK_CATALOG_BUCKET' in log for log in self.scheduler.get_logs())
        )

    def test_select_next_10_events_accepts_embas_from_source_sheet(self):
        now = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        tomorrow = now + timedelta(days=1)
        fecha = tomorrow.strftime('%d/%m/%y')

        result = self.scheduler.select_next_10_events([
            {
                'maestria': 'EMBAs',
                'fecha': fecha,
                'hora': '19',
                'fecha_hora': tomorrow,
                'row_idx': 2,
            }
        ])

        expected_date = fecha[:5]
        self.assertEqual(result['EMBARIF'], expected_date)
        self.assertEqual(result['REMBARIF'], expected_date)

    def test_select_next_events_maps_mbi_to_mbirif(self):
        now = datetime.now(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        event_date = now + timedelta(days=2)

        result = self.scheduler.select_next_10_events([{
            'maestria': 'MBI',
            'fecha': event_date.strftime('%d/%m/%Y'),
            'hora': '13:00',
            'fecha_hora': event_date,
            'row_idx': 2,
        }])

        self.assertEqual(result['MBIRIF'], event_date.strftime('%d/%m'))

    def test_select_next_events_normalizes_single_digit_dates(self):
        event_date = datetime(2026, 8, 13, 18, 30, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))

        result = self.scheduler.select_next_10_events([{
            'maestria': 'MBA SALUD',
            'fecha': '13/8/2026',
            'hora': '18:30',
            'fecha_hora': event_date,
            'row_idx': 2,
        }])

        self.assertEqual(result['MBASRIF'], '13/08')

    def test_platform_aliases_match_destination_ids(self):
        events = {
            'MBAORIF': '13/08',
            'MBASRIF': '13/08',
            'REMBARIF': '11/08',
        }

        meta = self.scheduler.get_platform_events(events, 'META')
        google = self.scheduler.get_platform_events(events, 'GGL')

        self.assertEqual(meta['MBARIF'], '13/08')
        self.assertEqual(google['MBAO'], '13/08')
        self.assertEqual(google['MBAS'], '13/08')
        self.assertEqual(google['EMBAR'], '11/08')

    def test_read_rif_data_uses_new_consolidado_header_row(self):
        self.scheduler.sheet_ops = Mock()
        self.scheduler.sheet_ops.read_sheet.return_value = [
            ['Maestria', 'Fecha de la RIF', 'Horario'],
            ['MBA', '13/08/2026', '19'],
        ]

        headers, rows = self.scheduler.read_rif_data()

        self.assertEqual(headers, ['Maestria', 'Fecha de la RIF', 'Horario'])
        self.assertEqual(rows, [['MBA', '13/08/2026', '19']])
        self.scheduler.sheet_ops.read_sheet.assert_called_once_with(
            sheet_id=Config.SOURCE_SHEET_ID,
            range_name=Config.RIF_SOURCE_RANGE,
            sheet_name=Config.SOURCE_SHEET_NAME,
            source=False,
        )

    def test_parse_new_consolidado_format_and_skip_cancelled_rows(self):
        headers = ['Maestria', 'Fecha de la RIF', 'Horario', 'Status']
        rows = [
            ['MBA', '13/08/2026', '19', 'Hecho'],
            ['FIN', '29/10/2026', '13:00', 'Cancelada'],
        ]

        events = self.scheduler.parse_rif_events(headers, rows)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['maestria'], 'MBA')
        self.assertEqual(events[0]['fecha_hora'].year, 2026)
        self.assertEqual(events[0]['fecha_hora'].hour, 19)

    def test_run_returns_false_when_any_output_fails(self):
        scheduler = RIFScheduler()
        scheduler.sheet_ops = object()

        with patch.object(scheduler, 'read_rif_data', return_value=(['header'], [['row']])), \
             patch.object(scheduler, 'parse_rif_events', return_value=[{'maestria': 'EMBA'}]), \
             patch.object(scheduler, 'select_next_10_events', return_value={'EMBARIF': '25/03'}), \
             patch.object(scheduler, 'update_descriptions', side_effect=[True, True]) as update_mock, \
             patch.object(scheduler, 'export_tiktok_catalog', return_value=False) as tiktok_mock:
            success = scheduler.run()

        self.assertFalse(success)
        self.assertEqual(update_mock.call_count, 2)
        tiktok_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
