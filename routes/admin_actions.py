import os
from flask import request, jsonify, session
from models import User
from users import hash_password
from db import db
from werkzeug.utils import secure_filename
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS

# ==========================================
# RUTAS DE ADMINISTRACIÓN – ACCIONES
# ==========================================

@bp.route('/api/admin/toggle_status/<int:user_id>', methods=['POST'])
def admin_toggle_status(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == session['user_id']:
        return jsonify({'error': 'No puedes bloquear tu propia cuenta principal'}), 400
    
    u = User.query.get_or_404(user_id)
    u.status = 'Bloqueado' if u.status == 'Activo' else 'Activo'
    db.session.commit()
    return jsonify({'success': True, 'new_status': u.status})


@bp.route('/api/admin/delete_user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == session['user_id']:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta principal'}), 400
        
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/api/admin/update_user/<int:user_id>', methods=['POST'])
def admin_update_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
        
    u = User.query.get_or_404(user_id)
    
    u.name = request.form.get('name', u.name)
    u.last_name_1 = request.form.get('last_name_1', u.last_name_1)
    u.last_name_2 = request.form.get('last_name_2', u.last_name_2)
    u.email = request.form.get('email', u.email).lower()
    
    new_role = request.form.get('role')
    if new_role:
        u.role = new_role
        if new_role == 'Superusuario': u.weight = 100
        elif new_role == 'Administrador 1': u.weight = 50
        elif new_role == 'Administrador 2': u.weight = 25
        elif new_role == 'Colaborador': u.weight = 10
        else: u.weight = 1
        
    new_pass = request.form.get('password')
    if new_pass:
        u.password_hash = hash_password(new_pass)
        
    if request.form.get('phone'): 
        u.phone = request.form.get('phone')
        
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"error": "Formato de imagen no permitido"}), 400
            
        filename = secure_filename(avatar_file.filename)
        filename = f"user_{u.id}_{filename}"
        static_folder = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
        os.makedirs(static_folder, exist_ok=True)
        avatar_file.save(os.path.join(static_folder, filename))
        u.avatar = f"uploads/{filename}"

    db.session.commit()
    return jsonify({'success': True})



@bp.route('/api/admin/create_user', methods=['POST'])
def admin_create_user():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json
    email = (data.get('email') or '').lower().strip()
    if not email or not data.get('name') or not data.get('last_name_1') or not data.get('password'):
        return jsonify({'error': 'Faltan datos obligatorios'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya registrado'}), 400
    try:
        from datetime import datetime
        new_user = User(
            name=data.get('name'),
            last_name_1=data.get('last_name_1'),
            last_name_2=data.get('last_name_2', ''),
            email=email,
            password_hash=hash_password(data.get('password'))
        )
        role = data.get('role', 'Usuario')
        new_user.role = role
        if role == 'Superusuario': new_user.weight = 100
        elif role == 'Administrador 1': new_user.weight = 50
        elif role == 'Administrador 2': new_user.weight = 25
        elif role == 'Colaborador': new_user.weight = 10
        else: new_user.weight = 1
        if data.get('phone'): new_user.phone = data.get('phone')
        if data.get('dob'):
            new_user.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date()
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True, 'id': new_user.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
