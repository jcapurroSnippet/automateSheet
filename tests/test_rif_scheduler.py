import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_export_tiktok_catalog_updates_csv_and_uploads_to_gcs(self):
        csv_content = "\n".join([
            "sku_id,title,description,additional_image_link",
            'EMBARIFV2,Executive MBA,Original,"https://img/a.png,https://img/b.png"',
            'MBASRIF,MBA Salud,Original,',
            'EMBA,Executive MBA,Keep,',
            "",
        ])

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "catalog.csv"
            source_path.write_text(csv_content, encoding='utf-8-sig')

            fake_client = FakeStorageClient()
            success = self.scheduler.export_tiktok_catalog(
                {
                    'EMBARIF': '25/03',
                    'MBASRIF': False,
                },
                source_file=str(source_path),
                bucket_name='bucket-test',
                object_name='catalogs/catalog_tiktok.csv',
                storage_client=fake_client
            )

        self.assertTrue(success)
        self.assertEqual(fake_client.last_bucket.name, 'bucket-test')
        self.assertEqual(fake_client.last_bucket.last_blob.object_name, 'catalogs/catalog_tiktok.csv')
        self.assertEqual(fake_client.last_bucket.last_blob.content_type, 'text/csv')

        uploaded_text = fake_client.last_bucket.last_blob.uploaded_bytes.decode('utf-8-sig')
        parsed_rows = list(csv.DictReader(io.StringIO(uploaded_text)))

        self.assertEqual(parsed_rows[0]['description'], 'Próxima reunión informativa: 25/03')
        self.assertEqual(parsed_rows[1]['description'], '')
        self.assertEqual(parsed_rows[2]['description'], 'Keep')
        self.assertEqual(
            parsed_rows[0]['additional_image_link'],
            'https://img/a.png,https://img/b.png'
        )
        self.assertEqual(
            list(parsed_rows[0].keys()),
            ['sku_id', 'title', 'description', 'additional_image_link']
        )

    def test_export_tiktok_catalog_fails_when_bucket_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "catalog.csv"
            source_path.write_text(
                "sku_id,title,description\nEMBARIF,Executive MBA,Original\n",
                encoding='utf-8-sig'
            )

            with patch.object(Config, 'TIKTOK_CATALOG_BUCKET', ''):
                success = self.scheduler.export_tiktok_catalog(
                    {'EMBARIF': '25/03'},
                    source_file=str(source_path),
                    bucket_name=''
                )

        self.assertFalse(success)
        self.assertTrue(
            any('TIKTOK_CATALOG_BUCKET' in log for log in self.scheduler.get_logs())
        )

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
