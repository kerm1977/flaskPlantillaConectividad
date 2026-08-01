import json
import uuid
from urllib.parse import quote
from datetime import date
from flask import request, jsonify
from models import Form, FormField, FormResponse, FormAnswer, Hiker
from db import db
from routes import bp


@bp.route('/api/forms/<int:form_id>/submit', methods=['POST'])
def api_submit_form(form_id):
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Este formulario está cerrado'}), 403

    data         = request.get_json() or {}
    answers_data = data.get('answers', {})
    edit_token   = uuid.uuid4().hex
    cedula_valor = data.get('cedula', '').strip()
    nombre_valor = data.get('nombre_completo', '').strip()

    response = FormResponse(
        form_id=form_id, edit_token=edit_token,
        nombre_completo=nombre_valor,
        cedula=cedula_valor or None,
        email=data.get('email', ''),
        telefono=data.get('telefono', ''),
        edad=int(data.get('edad')) if data.get('edad') else None,
        tipo_sangre=data.get('tipo_sangre', '') or None,
        alergias=data.get('alergias', '') or None,
        enfermedades_cronicas=data.get('enfermedades_cronicas', '') or None,
        contacto_emergencia_nombre=data.get('contacto_emergencia_nombre', '') or None,
        contacto_emergencia_telefono=data.get('contacto_emergencia_telefono', '') or None,
        pasaporte=data.get('pasaporte', '') or None,
        fecha_nacimiento_dia=int(data.get('fecha_nacimiento_dia')) if data.get('fecha_nacimiento_dia') else None,
        fecha_nacimiento_mes=int(data.get('fecha_nacimiento_mes')) if data.get('fecha_nacimiento_mes') else None,
        fecha_nacimiento_anio=int(data.get('fecha_nacimiento_anio')) if data.get('fecha_nacimiento_anio') else None,
    )

    if cedula_valor and nombre_valor:
        _upsert_hiker(data, cedula_valor, nombre_valor)

    _save_answers_and_score(form, response, answers_data)
    db.session.add(response)
    db.session.commit()

    summary_text = _build_summary(form, answers_data)
    result = _build_response(form, response, data, summary_text)
    return jsonify(result)


def _upsert_hiker(data, cedula, nombre):
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    fecha_nacimiento = None
    if data.get('fecha_nacimiento_dia') and data.get('fecha_nacimiento_mes') and data.get('fecha_nacimiento_anio'):
        try:
            fecha_nacimiento = date(
                int(data.get('fecha_nacimiento_anio')),
                int(data.get('fecha_nacimiento_mes')),
                int(data.get('fecha_nacimiento_dia'))
            )
        except ValueError:
            pass

    if not hiker:
        hiker = Hiker(
            cedula=cedula,
            nombre_completo=nombre,
            telefono=data.get('telefono', '') or None,
            pasaporte=data.get('pasaporte', '') or None,
            tipo_sangre=data.get('tipo_sangre', '') or None,
            fecha_nacimiento=fecha_nacimiento,
            alergias=data.get('alergias', '') or None,
            enfermedades_cronicas=data.get('enfermedades_cronicas', '') or None,
            contacto_emergencia_nombre=data.get('contacto_emergencia_nombre', '') or None,
            contacto_emergencia_telefono=data.get('contacto_emergencia_telefono', '') or None
        )
        db.session.add(hiker)
    else:
        _update_hiker(hiker, data, fecha_nacimiento)


def _update_hiker(hiker, data, fecha_nacimiento):
    for field, key in [
        ('telefono', 'telefono'),
        ('pasaporte', 'pasaporte'),
        ('tipo_sangre', 'tipo_sangre'),
        ('alergias', 'alergias'),
        ('enfermedades_cronicas', 'enfermedades_cronicas'),
        ('contacto_emergencia_nombre', 'contacto_emergencia_nombre'),
        ('contacto_emergencia_telefono', 'contacto_emergencia_telefono'),
    ]:
        if data.get(key) and not getattr(hiker, field):
            setattr(hiker, field, data.get(key))
    if fecha_nacimiento and not hiker.fecha_nacimiento:
        hiker.fecha_nacimiento = fecha_nacimiento


def _save_answers_and_score(form, response, answers_data):
    fields = FormField.query.filter_by(form_id=form.id).order_by(FormField.order).all()
    score = total_graded = 0
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        answer = FormAnswer(
            field_id=field.id,
            value=json.dumps(answer_value, ensure_ascii=False)
                  if isinstance(answer_value, list) else str(answer_value)
        )
        response.answers.append(answer)
        if form.form_type == 'examen' and field.correct_answer:
            total_graded += 1
            if field.field_type == 'checkbox':
                correct = sorted(json.loads(field.correct_answer)) if field.correct_answer else []
                given = sorted(answer_value) if isinstance(answer_value, list) else []
                if correct == given:
                    score += 1
            elif str(answer_value).strip().lower() == field.correct_answer.strip().lower():
                score += 1
    if form.form_type == 'examen' and total_graded > 0:
        response.score = round((score / total_graded) * 100, 1)
        response.total_questions = total_graded


def _build_summary(form, answers_data):
    lines = []
    for field in FormField.query.filter_by(form_id=form.id).order_by(FormField.order).all():
        v = answers_data.get(str(field.id), '')
        display = ', '.join(v) if isinstance(v, list) else str(v)
        if display:
            lines.append(f"• {field.label}: {display}")
    return '\n'.join(lines)


def _build_response(form, response, data, summary_text):
    nombre = data.get('nombre_completo', '')
    edit_url = f"{request.host_url}form/{form.slug or form.id}/editar/{response.edit_token}"
    result = {
        'ok': True,
        'response_id': response.id,
        'edit_token': response.edit_token,
        'answers_summary': summary_text,
        'nombre': nombre
    }
    if form.form_type == 'examen':
        correct = round((response.score or 0) / 100 * (response.total_questions or 0))
        result.update({'score': response.score, 'correct': correct, 'total': response.total_questions})

    telefono = data.get('telefono', '').strip().replace(' ', '').replace('-', '')
    if telefono and telefono[0] in ('6', '7', '8'):
        msg = f"📋 *{form.name}*\n\nHola *{nombre or 'participante'}*, este mensaje es para ti.\n"
        msg += f"El sistema ya registró tu selección:\n\n{summary_text}\n\n"
        if form.form_type == 'examen' and response.score is not None:
            msg += f"📊 Calificación: {response.total_questions}... ({response.score}%)\n\n"
        if form.allow_edit and form.form_type != 'examen':
            msg += f"✏️ Si deseas cambiar tu selección, usa este enlace:\n{edit_url}\n\n"
        msg += "✅ Gracias por completar el formulario."
        if not telefono.startswith('+'):
            telefono = '506' + telefono
        result['whatsapp_url'] = f"https://wa.me/{telefono}?text={quote(msg)}"

    admin_msg = f"📋 *{form.name}*\nRespuesta de: *{nombre or 'Anónimo'}*\n\n{summary_text}\n"
    if form.form_type == 'examen' and response.score is not None:
        admin_msg += f"\n📊 Nota: {response.score}%\n"
    result['admin_msg'] = quote(admin_msg)
    return result
