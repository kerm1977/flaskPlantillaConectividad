import secrets
from datetime import datetime, timedelta
from urllib.parse import quote
from flask import request, jsonify, render_template
from models import User
from db import db
from routes import bp


@bp.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'ok': False, 'error': 'No existe una cuenta con ese correo'}), 404

    token = secrets.token_hex(20)
    expires = (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    user.reset_token = token
    user.reset_expires = expires
    db.session.commit()

    reset_url = f"{request.host_url}reset/{token}"
    phone = (user.whatsapp or user.phone or '').strip().replace(' ', '').replace('-', '')
    if phone and not phone.startswith('+'):
        phone = '506' + phone

    result = {'ok': True, 'reset_url': reset_url}
    if phone:
        msg = ("\U0001f510 *Recuperar Contrase\u00f1a*\n\n"
               f"Hola {user.name}, usa este enlace para crear una nueva contrase\u00f1a:\n"
               f"{reset_url}\n\n"
               "\u23f1\ufe0f V\u00e1lido por 2 horas. Si no solicitaste esto, ign\u00f3ralo.")
        result['whatsapp_url'] = f"https://wa.me/{phone}?text={quote(msg)}"
    return jsonify(result)


@bp.route('/reset/<token>', methods=['GET'])
def reset_password_page(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_expires:
        return render_template('reset_password.html', valid=False, token=token)
    try:
        expires = datetime.strptime(user.reset_expires, '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires:
            return render_template('reset_password.html', valid=False, token=token)
    except Exception:
        return render_template('reset_password.html', valid=False, token=token)
    return render_template('reset_password.html', valid=True, token=token, user_name=user.name)


@bp.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token', '')
    new_pass = data.get('password', '').strip()

    from security import validate_password_strength
    valid, msg = validate_password_strength(new_pass)
    if not valid:
        return jsonify({'ok': False, 'error': msg}), 400
    if not token:
        return jsonify({'ok': False, 'error': 'Token requerido'}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'ok': False, 'error': 'Token inválido o expirado'}), 400
    try:
        expires = datetime.strptime(user.reset_expires, '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires:
            return jsonify({'ok': False, 'error': 'El enlace ha expirado'}), 400
    except Exception:
        return jsonify({'ok': False, 'error': 'Token inválido'}), 400

    from users import hash_password
    user.password_hash = hash_password(new_pass)
    user.reset_token = None
    user.reset_expires = None
    db.session.commit()
    return jsonify({'ok': True})
