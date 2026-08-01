import os
from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename
from models import Form, FormResponse, Hiker
from routes import bp, _PROJECT_ROOT

FORM_UPLOADS = os.path.join(_PROJECT_ROOT, 'static', 'uploads', 'forms')


# ── VISTAS PÚBLICAS ──────────────────────────────────────────────────────────

@bp.route('/form/<path:slug>/editar/<token>')
def public_form_edit(slug, token):
    resp = FormResponse.query.filter_by(edit_token=token).first_or_404()
    form = Form.query.get_or_404(resp.form_id)
    if form.form_type == 'examen' or not form.allow_edit:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form, edit_token=token, edit_response_id=resp.id)


@bp.route('/form/<path:slug>')
def public_form(slug):
    form = Form.query.get_or_404(int(slug)) if slug.isdigit() else \
           Form.query.filter_by(slug=slug).first_or_404()
    if not form.is_active:
        return render_template('form_closed.html', form=form)
    return render_template('form_public.html', form=form)


# ── SUBIR ARCHIVO ────────────────────────────────────────────────────────────

@bp.route('/api/forms/<int:form_id>/submit_file', methods=['POST'])
def api_submit_file(form_id):
    form = Form.query.get_or_404(form_id)
    if not form.is_active:
        return jsonify({'error': 'Formulario cerrado'}), 403
    file     = request.files.get('file')
    field_id = request.form.get('field_id')
    if not file or not field_id:
        return jsonify({'error': 'Datos incompletos'}), 400
    os.makedirs(FORM_UPLOADS, exist_ok=True)
    filename = secure_filename(f"f{form_id}_{field_id}_{file.filename}")
    file.save(os.path.join(FORM_UPLOADS, filename))
    return jsonify({'ok': True, 'path': f"uploads/forms/{filename}"})


# ── BUSCAR HIKERS (AUTOCOMPLETE EN FORMULARIOS) ──────────────────────────────

@bp.route('/api/forms/search_hikers')
def api_search_hikers():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    hikers = (Hiker.query.filter(Hiker.cedula.contains(q)).limit(10).all()
              if q.isdigit() else
              Hiker.query.filter(Hiker.nombre_completo.ilike(f'%{q}%')).limit(10).all())
    return jsonify([{'cedula': h.cedula, 'nombre_completo': h.nombre_completo,
                     'telefono': h.telefono or '', 'email': ''} for h in hikers])
