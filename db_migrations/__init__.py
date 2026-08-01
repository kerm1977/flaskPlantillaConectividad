from .raffle import migrate_raffle_selection
from .user import migrate_user_reset
from .publicacion import migrate_publicacion
from .forms import migrate_forms_ficha_medica, migrate_forms_pasaporte_fecha_nacimiento
from .hiker import migrate_hiker_pasaporte
from .form_response import migrate_form_response_reservation_number
from .event import migrate_event_date_changes


def run_all():
    """Ejecuta todas las migraciones aditivas sin borrar datos."""
    migrate_raffle_selection()
    migrate_user_reset()
    migrate_publicacion()
    migrate_forms_ficha_medica()
    migrate_forms_pasaporte_fecha_nacimiento()
    migrate_hiker_pasaporte()
    migrate_form_response_reservation_number()
    migrate_event_date_changes()
