import os
from flask import request, jsonify, session
from models import User
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS


@bp.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        user.name = request.form.get('name', user.name)
        user.last_name_1 = request.form.get('last_name_1', user.last_name_1)
        user.last_name_2 = request.form.get('last_name_2', user.last_name_2)
        user.email = request.form.get('email', user.email).lower()

        if request.form.get('phone_code'):
            user.phone_code = request.form.get('phone_code')
        if request.form.get('phone'):
            user.phone = request.form.get('phone')

        dob_str = request.form.get('dob')
        if dob_str:
            from datetime import datetime
            user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

        for field in ['whatsapp', 'facebook', 'instagram', 'address', 'institution', 'other_info']:
            value = request.form.get(field)
            if value and hasattr(user, field):
                setattr(user, field, value)

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400

            filename = secure_filename(avatar_file.filename)
            filename = f"user_{user.id}_{filename}"
            static_folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(static_folder, exist_ok=True)
            filepath = os.path.join(static_folder, filename)
            avatar_file.save(filepath)
            user.avatar = f"uploads/{filename}"

        db.session.commit()
        session['avatar'] = user.avatar or 'default.png'
        return jsonify({'success': True})

    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error interno al guardar los datos'}), 500
