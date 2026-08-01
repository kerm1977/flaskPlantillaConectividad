import json
from io import BytesIO
from flask import request, jsonify, session, Response, send_file
from models import Form, FormField, FormResponse
from routes import bp
from routes.forms_responses_utils import _build_answers_map
from routes.forms_responses_export_small import _export_json, _export_xlsx, _export_whatsapp
from routes.forms_responses_export_pdf import _export_pdf
from routes.forms_responses_export_txt import _export_txt


@bp.route('/api/forms/<int:form_id>/export/<fmt>')
def api_export_responses(form_id, fmt):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    form = Form.query.get_or_404(form_id)
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    responses = FormResponse.query.filter_by(form_id=form_id).order_by(
                FormResponse.submitted_at.desc()).all()
    add_membrete = request.args.get('membrete', 'true').lower() == 'true'
    include_fecha = request.args.get('include_fecha', 'true').lower() == 'true'
    include_ficha_medica = request.args.get('include_ficha_medica', 'true').lower() == 'true'

    if fmt == 'json':
        return _export_json(form, fields, responses)
    if fmt == 'xlsx':
        return _export_xlsx(form, fields, responses)
    if fmt == 'whatsapp':
        return _export_whatsapp(form, fields, responses, include_fecha, include_ficha_medica)
    if fmt == 'pdf':
        return _export_pdf(form, fields, responses, add_membrete, include_fecha, include_ficha_medica)
    if fmt == 'txt':
        return _export_txt(form, fields, responses, add_membrete, include_fecha, include_ficha_medica)
    return jsonify({'error': 'Formato no soportado'}), 400
