import json
from io import BytesIO
from flask import request, jsonify, Response, send_file
from models import Form, FormField, FormResponse
from routes.forms_responses_utils import _build_answers_map

def _export_json(*args, **kwargs):
    rows = []
    for r in responses:
        row = {'nombre': r.nombre_completo}
        if form.show_cedula:
            row['cedula'] = r.cedula or ''
        row['reservation_number'] = r.reservation_number or ''
        row.update({'email': r.email, 'telefono': r.telefono,
                    'edad': r.edad, 'fecha': r.submitted_at.isoformat() if r.submitted_at else '',
                    'score': r.score})
        if form.show_ficha_medica:
            row.update({'tipo_sangre': r.tipo_sangre or '', 'alergias': r.alergias or '',
                        'enfermedades_cronicas': r.enfermedades_cronicas or '',
                        'contacto_emergencia_nombre': r.contacto_emergencia_nombre or '',
                        'contacto_emergencia_telefono': r.contacto_emergencia_telefono or ''})
        for f in fields:
            val = _build_answers_map(r, [f]).get(str(f.id), '')
            row[f.label] = val
        rows.append(row)
    raw = json.dumps(rows, ensure_ascii=False, indent=2)
    return Response(raw, mimetype='application/json',
                    headers={'Content-Disposition': f'attachment; filename="{form.name}.json"'})


def _export_xlsx(*args, **kwargs):
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = form.name[:30]
        headers = ['Nombre']
        if form.show_cedula:
            headers.append('Cédula')
        headers.append('Número de Reserva')
        headers += ['Email', 'Teléfono', 'Edad', 'Fecha']
        if form.form_type == 'examen':
            headers.append('Calificación')
        if form.show_ficha_medica:
            headers += ['Tipo de Sangre', 'Alergias', 'Enfermedades Crónicas',
                        'Contacto Emergencia Nombre', 'Contacto Emergencia Teléfono']
        headers += [f.label for f in fields]
        ws.append(headers)
        for r in responses:
            row = [r.nombre_completo]
            if form.show_cedula:
                row.append(r.cedula or '')
            row.append(r.reservation_number or '')
            row += [r.email, r.telefono, r.edad,
                    r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '']
            if form.form_type == 'examen':
                row.append(f"{r.score}%" if r.score is not None else '')
            if form.show_ficha_medica:
                row += [r.tipo_sangre or '', r.alergias or '', r.enfermedades_cronicas or '',
                       r.contacto_emergencia_nombre or '', r.contacto_emergencia_telefono or '']
            for f in fields:
                val = _build_answers_map(r, [f]).get(str(f.id), '')
                if isinstance(val, list):
                    val = ', '.join(val)
                row.append(val)
            ws.append(row)
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{form.name}.xlsx",
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except ImportError:
        return jsonify({'error': 'openpyxl no instalado. Ejecute: pip install openpyxl'}), 500


def _export_whatsapp(*args, **kwargs):
    lines = [f"📋 *{form.name}*", f"Respuestas: {len(responses)}", ""]
    for i, r in enumerate(responses[:50], 1):
        lines.append(f"*{i}. {r.nombre_completo or 'Anónimo'}*")
        if r.reservation_number:
            lines.append(f"   🎫 Número de Reserva: {r.reservation_number}")
        if include_fecha and r.submitted_at:
            lines.append(f"   📅 Fecha: {r.submitted_at.strftime('%d/%m/%Y %H:%M')}")
        if form.form_type == 'examen' and r.score is not None:
            lines.append(f"   📊 Nota: {r.score}%")
        if include_ficha_medica and form.show_ficha_medica:
            if r.tipo_sangre:
                lines.append(f"   🩸 Tipo Sangre: {r.tipo_sangre}")
            if r.alergias:
                lines.append(f"   ⚠️ Alergias: {r.alergias}")
            if r.enfermedades_cronicas:
                lines.append(f"   💊 Enf. Crónicas: {r.enfermedades_cronicas}")
        for f in fields:
            val = _build_answers_map(r, [f]).get(str(f.id), '')
            if isinstance(val, list):
                val = ', '.join(val)
            lines.append(f"   • {f.label}: {val}")
        lines.append("")
    return jsonify({'text': '\n'.join(lines)})


