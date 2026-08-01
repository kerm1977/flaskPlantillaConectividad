import json
from flask import jsonify, session
from models import Form, FormField, FormResponse
from db import db
from routes import bp
from routes.forms_responses_utils import _build_answers_map


@bp.route('/api/forms/<int:form_id>/responses')
def api_get_responses(form_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(
                FormResponse.submitted_at.desc()).all()
    output = []
    for r in responses:
        row = {'id': r.id, 'nombre_completo': r.nombre_completo, 'cedula': r.cedula or '',
               'email': r.email, 'telefono': r.telefono, 'edad': r.edad,
               'tipo_sangre': r.tipo_sangre or '', 'alergias': r.alergias or '',
               'enfermedades_cronicas': r.enfermedades_cronicas or '',
               'contacto_emergencia_nombre': r.contacto_emergencia_nombre or '',
               'contacto_emergencia_telefono': r.contacto_emergencia_telefono or '',
               'pasaporte': r.pasaporte or '',
               'fecha_nacimiento_dia': r.fecha_nacimiento_dia,
               'fecha_nacimiento_mes': r.fecha_nacimiento_mes,
               'fecha_nacimiento_anio': r.fecha_nacimiento_anio,
               'reservation_number': r.reservation_number or '',
               'submitted_at': r.submitted_at.strftime('%d/%m/%Y %H:%M') if r.submitted_at else '',
               'score': r.score, 'total_questions': r.total_questions,
               'answers': _build_answers_map(r, fields)}
        output.append(row)
    fields_info = [{'id': f.id, 'label': f.label, 'field_type': f.field_type,
                    'options': json.loads(f.options) if f.options else []} for f in fields]
    return jsonify({'fields': fields_info, 'responses': output,
                    'show_cedula': form.show_cedula, 'show_ficha_medica': form.show_ficha_medica,
                    'show_pasaporte': form.show_pasaporte, 'show_fecha_nacimiento': form.show_fecha_nacimiento})
