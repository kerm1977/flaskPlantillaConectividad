import json
from io import BytesIO
from flask import request, jsonify, Response, send_file
from models import Form, FormField, FormResponse
from routes.forms_responses_utils import _build_answers_map

def _export_txt(*args, **kwargs):
    lines = []
    if add_membrete:
        lines.append("=" * 60)
        lines.append("La Tribu de Los Libres")
        lines.append("Cartago, La Unión, San Diego")
        lines.append("86227500 -")
        lines.append("")
        lines.append("Responsables")
        lines.append("Kenneth Ruiz Matamoros - 86227500")
        lines.append("Jenny Ceciliano Cordoba - 86520937")
        lines.append("lthikingcr@gmail.com")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
    lines.append(f"FORMULARIO: {form.name}")
    lines.append(f"Cantidad Personas == {len(responses)} Respuestas")
    # Números de reserva si existen (desde parámetro)
    reservation_numbers = request.args.get('reservation_numbers', '')
    if reservation_numbers:
        lines.append(f"Números de Reserva: {reservation_numbers}")
    lines.append("=" * 60)
    lines.append("")
    
    for i, r in enumerate(responses, 1):
        lines.append(f"#{i} - {r.nombre_completo or 'Sin nombre'}")
        if r.reservation_number:
            lines.append(f"Número de Reserva: {r.reservation_number}")
        if form.show_cedula and r.cedula:
            lines.append(f"Cédula: {r.cedula}")
        if r.email:
            lines.append(f"Email: {r.email}")
        if r.telefono:
            lines.append(f"Teléfono: {r.telefono}")
        if include_fecha and r.edad:
            lines.append(f"Edad: {r.edad}")
        if include_fecha and r.submitted_at:
            lines.append(f"Fecha: {r.submitted_at.strftime('%d/%m/%Y %H:%M')}")
        if form.form_type == 'examen' and r.score is not None:
            lines.append(f"Calificación: {r.score}%")
        if include_ficha_medica and form.show_ficha_medica:
            lines.append("Ficha Médica:")
            if r.tipo_sangre:
                lines.append(f"  Tipo de Sangre: {r.tipo_sangre}")
            if r.alergias:
                lines.append(f"  Alergias: {r.alergias}")
            if r.enfermedades_cronicas:
                lines.append(f"  Enfermedades Crónicas: {r.enfermedades_cronicas}")
            if r.contacto_emergencia_nombre:
                lines.append(f"  Contacto Emergencia: {r.contacto_emergencia_nombre} {r.contacto_emergencia_telefono or ''}")
        for f in fields:
            val = _build_answers_map(r, [f]).get(str(f.id), '')
            if isinstance(val, list):
                val = ', '.join(val)
            if val:
                lines.append(f"{f.label}: {val}")
        lines.append("-" * 40)
        lines.append("")
    
    content = '\n'.join(lines)
    return Response(content, mimetype='text/plain',
                    headers={'Content-Disposition': f'attachment; filename="{form.name}.txt"'})

