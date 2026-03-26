"""
Módulo para subir imágenes de programas RIF a GCS y actualizar los sheets.
Actualiza META (image_link + additional_image_link con |),
GGL (image url, solo 1:1) y TikTok se resuelve automáticamente
al exportar desde META (convierte | a ,).
"""

import os
from datetime import datetime
from config_rif import RIFConfig as Config


class ImageUploader:
    PROGRAM_NAMES = {
        'EDNRIF': 'EDN',
        'EMBARIF': 'EMBA',
        'REMBARIF': 'REMBA',
        'MBAORIF': "MBA's",
        'MBASRIF': 'MBA Salud',
        'MIMRIF': 'MIM',
        'MKTRIF': 'MKT',
        'MNDRIF': 'MND',
        'RRHHRIF': 'MRHH',
        'FLRIF': 'Fin&Law / FyL',
        'FINRIF': 'MFIN',
        'MBTRIF': 'MBT',
        'OSFLRIF': 'MOSFL',
        'FINORIF': 'MF Online',
        # Variantes V2 (piezas distintas)
        'EMBARIFV2': 'EMBA V2',
        'REMBARIFV2': 'REMBA V2',
        'MBAORIFV2': "MBA's V2",
        'MBASRIFV2': 'MBA Salud V2',
        'MIMRIFV2': 'MIM V2',
        'MKTRIFV2': 'MKT V2',
        'MNDRIFV2': 'MND V2',
        'RRHHRIFV2': 'MRHH V2',
        'FLRIFV2': 'Fin&Law / FyL V2',
        'FINRIFV2': 'MFIN V2',
        'MBTRIFV2': 'MBT V2',
        'OSFLRIFV2': 'MOSFL V2',
        'FINORIFV2': 'MF Online V2',
    }

    CONTENT_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }

    def __init__(self, sheet_ops):
        self.sheet_ops = sheet_ops
        # Mapeo inverso: RIF ID -> GGL ID (ej: EMBARIF -> EMBA)
        self._rif_to_ggl = {}
        for ggl_id, rif_ids in Config.map_rif.items():
            for rif_id in rif_ids:
                self._rif_to_ggl[rif_id] = ggl_id

    # ── Lectura de sheets ────────────────────────────────────────────

    def _read_sheet(self, sheet_id, range_name, sheet_name):
        return self.sheet_ops.read_sheet(sheet_id, range_name, sheet_name, False)

    def get_programs(self):
        """Devuelve todos los programas. Si el sheet se puede leer, incluye imágenes actuales."""
        # Siempre mostrar todos los programas
        programs = {
            pid: {'id': pid, 'name': name, 'image_link': '', 'additional_image_link': ''}
            for pid, name in self.PROGRAM_NAMES.items()
        }

        # Intentar leer imágenes actuales del sheet META
        try:
            if not self.sheet_ops:
                raise RuntimeError("Sin conexión al sheet")
            data = self._read_sheet(
                Config.DESTINATION_SHEET_ID_META,
                Config.RIF_DEST_RANGE_META,
                Config.DESTINATION_SHEET_NAME_META,
            )
            if data:
                headers = data[0]
                rows = data[1:]
                header_map = {h.strip().lower(): i for i, h in enumerate(headers)}

                id_idx = header_map.get('id', 0)
                img_idx = header_map.get('image_link')
                add_img_idx = header_map.get('additional_image_link')

                for row in rows:
                    if len(row) <= id_idx:
                        continue
                    row_id = row[id_idx].strip()
                    if row_id in programs:
                        if img_idx is not None and img_idx < len(row):
                            programs[row_id]['image_link'] = row[img_idx]
                        if add_img_idx is not None and add_img_idx < len(row):
                            programs[row_id]['additional_image_link'] = row[add_img_idx]
        except Exception as e:
            print(f"No se pudieron leer imágenes del sheet: {e}")

        return sorted(programs.values(), key=lambda p: p['name'])

    # ── Upload a GCS ─────────────────────────────────────────────────

    def _get_content_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return self.CONTENT_TYPES.get(ext, 'application/octet-stream')

    def _upload_to_gcs(self, file_data, gcs_path, content_type):
        from google.cloud import storage

        bucket_name = Config.IMAGE_BUCKET
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(file_data, content_type=content_type)

        return f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"

    # ── Subida + actualización de sheets ─────────────────────────────

    def upload_and_update(self, program_id, image_1x1=None, images_additional=None):
        """Sube imágenes a GCS y actualiza META y GGL."""
        results = {'1x1': None, 'additional': None}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if image_1x1 and image_1x1.filename:
            ext = os.path.splitext(image_1x1.filename)[1].lower()
            gcs_path = f"{program_id}/1x1_{timestamp}{ext}"
            content_type = self._get_content_type(image_1x1.filename)
            url = self._upload_to_gcs(image_1x1.read(), gcs_path, content_type)

            # META: columna image_link
            self._update_column(
                Config.DESTINATION_SHEET_ID_META, Config.RIF_DEST_RANGE_META,
                Config.DESTINATION_SHEET_NAME_META,
                program_id, 'image_link', url, 'META',
            )
            # GGL: columna image url (solo 1:1)
            self._update_column(
                Config.DESTINATION_SHEET_ID_GGL, Config.RIF_DEST_RANGE_GGL,
                Config.DESTINATION_SHEET_NAME_GGL,
                program_id, 'image url', url, 'GGL',
            )
            results['1x1'] = url

        if images_additional:
            urls = []
            for i, img_file in enumerate(images_additional):
                if not img_file.filename:
                    continue
                ext = os.path.splitext(img_file.filename)[1].lower()
                gcs_path = f"{program_id}/add_{timestamp}_{i}{ext}"
                content_type = self._get_content_type(img_file.filename)
                url = self._upload_to_gcs(img_file.read(), gcs_path, content_type)
                urls.append(url)

            if urls:
                # META: additional_image_link separado por |
                self._update_column(
                    Config.DESTINATION_SHEET_ID_META, Config.RIF_DEST_RANGE_META,
                    Config.DESTINATION_SHEET_NAME_META,
                    program_id, 'additional_image_link', '|'.join(urls), 'META',
                )
                # TikTok se resuelve solo: export_tiktok_catalog lee de META
                # y convierte | a , en normalize_additional_image_link
                results['additional'] = '|'.join(urls)

        return results

    # ── Actualización genérica de columna ────────────────────────────

    def _matches_program(self, row_id, program_id, platform):
        """Verifica si un ID de fila corresponde al programa, según la plataforma."""
        row_id = row_id.strip()
        # Match exacto por ID
        if row_id == program_id:
            return True
        # En GGL los IDs son más cortos (EMBA, MKT, etc.)
        # Normalizar sin V2 para buscar en el mapeo
        base_id = program_id.replace('V2', '').strip()
        if platform == 'GGL' and base_id in self._rif_to_ggl:
            return row_id == self._rif_to_ggl[base_id]
        return False

    def _update_column(self, sheet_id, range_name, sheet_name,
                        program_id, column_name, value, platform):
        """Actualiza una columna en todas las filas que matchean el programa."""
        data = self._read_sheet(sheet_id, range_name, sheet_name)
        if not data:
            print(f"No se pudo leer el sheet {sheet_name} para actualizar {column_name}")
            return False

        headers = data[0]
        rows = data[1:]
        header_map = {h.strip().lower(): i for i, h in enumerate(headers)}

        id_idx = header_map.get('id', 0)
        target_idx = header_map.get(column_name.lower())

        if target_idx is None:
            print(f"Columna '{column_name}' no encontrada en {sheet_name}")
            return False

        num_cols = len(headers)
        updated = False

        for row in rows:
            if len(row) <= id_idx:
                continue
            if self._matches_program(row[id_idx], program_id, platform):
                while len(row) < num_cols:
                    row.append('')
                row[target_idx] = value
                updated = True

        if updated:
            self.sheet_ops.write_sheet(
                sheet_id, [headers] + rows, range_name, sheet_name,
            )

        return updated
