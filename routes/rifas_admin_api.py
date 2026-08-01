import json
from flask import request, jsonify, session
from models import Raffle, RaffleSelection, User
from db import db
from routes import bp


def _check_rifa_admin():
    user = User.query.get(session.get('user_id'))
    if not user or user.email not in ['kenth1977@gmail.com', 'lthikingcr@gmail.com']:
        return False
    return True


@bp.route('/admin/rifas/<int:raffle_id>/ganadores', methods=['POST'])
def establecer_ganadores(raffle_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    rifa = Raffle.query.get_or_404(raffle_id)
    data = request.get_json()
    rifa.winning_numbers = json.dumps(data.get('winners', []))
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/rifas/<int:raffle_id>/find-winner/<string:number>', methods=['GET'])
def find_winner(raffle_id, number):
    if not _check_rifa_admin():
        return jsonify({'error': 'No autorizado'}), 403
    num = number.zfill(2)
    selection = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, number=num, is_canceled=False).first()
    if selection:
        return jsonify({'winner': {'name': selection.customer_name,
                                   'phone': selection.customer_phone,
                                   'cedula': selection.customer_cedula or ''}})
    return jsonify({'winner': None})


@bp.route('/api/rifas/<int:raffle_id>/toggle-payment/<string:phone>', methods=['POST'])
def toggle_payment(raffle_id, phone):
    if not _check_rifa_admin():
        return jsonify({'error': 'No autorizado'}), 403
    selections = RaffleSelection.query.filter_by(
        raffle_id=raffle_id, customer_phone=phone).all()
    if not selections:
        return jsonify({'error': 'Selección no encontrada'}), 404
    new_status = not all(sel.is_paid for sel in selections)
    for sel in selections:
        sel.is_paid = new_status
    db.session.commit()
    return jsonify({'ok': True, 'is_paid': new_status, 'is_canceled': any(s.is_canceled for s in selections)})
