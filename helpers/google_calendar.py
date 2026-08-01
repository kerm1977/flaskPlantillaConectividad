from helpers.google_calendar_core import _parse_date_str, build_google_calendar_url


def generate_google_calendar_link_pub(pub):
    """Genera enlace Google Calendar desde una Publicacion."""
    title = pub.nombre or "Actividad"
    start_date = pub.fecha_inicio
    end_date = pub.fecha_fin
    if start_date and not end_date:
        from datetime import timedelta
        end_date = start_date + timedelta(days=1)

    parts = [f"Nombre del Lugar: {pub.nombre}"]
    for field, label in [
        ('tipo_evento', 'Actividad'), ('lugar', 'Lugar'), ('punto_salida', 'Lugar de Salida'),
        ('hora_encuentro', 'Hora de Salida'), ('descripcion', 'Descripción'),
        ('recomendaciones', 'Recomendaciones'), ('desc_caminata', 'Detalles de la caminata'),
        ('telefono', 'Teléfono'), ('whatsapp', 'WhatsApp'), ('direccion', 'Dirección')
    ]:
        value = getattr(pub, field)
        if value:
            parts.append(f"{label}: {value}")
    if pub.fecha_inicio:
        fecha_str = pub.fecha_inicio.strftime('%d/%m/%Y')
        if pub.fecha_fin:
            fecha_str += f" al {pub.fecha_fin.strftime('%d/%m/%Y')}"
        parts.append(f"Fecha de Actividad: {fecha_str}")

    location = pub.lugar or pub.punto_salida or pub.direccion or ""
    return build_google_calendar_url(title, start_date, end_date, parts, location)


def generate_google_calendar_link_event(event):
    """Genera enlace Google Calendar desde un Event."""
    title = event.nombre_lugar or event.actividad or "Actividad"
    if event.dias == 1 and event.fecha_unica:
        start_date = _parse_date_str(event.fecha_unica)
    else:
        start_date = _parse_date_str(event.fecha_inicio)
    end_date = _parse_date_str(event.fecha_regreso)

    parts = [f"Nombre del Lugar: {event.nombre_lugar}"]
    for field, label in [
        ('actividad', 'Actividad'), ('dificultad', 'Dificultad'), ('moneda', 'Moneda'),
        ('precio', 'Precio'), ('reserva', 'Reserva'), ('capacidad', 'Capacidad'),
        ('hora_salida', 'Hora de Salida'), ('lugar_salida', 'Lugar de Salida'),
        ('puntos_recogida', 'Puntos de recogida'), ('itinerario', 'Itinerario'),
        ('incluye', 'Incluye')
    ]:
        value = getattr(event, field)
        if value:
            parts.append(f"{label}: {value}")
    if event.dias:
        parts.append(f"Cantidad de Días: {event.dias}")
    if event.fecha_unica and event.dias == 1:
        parts.append(f"Fecha de Actividad: {event.fecha_unica}")
    elif event.fecha_inicio and event.fecha_regreso:
        parts.append(f"Fecha de Actividad: {event.fecha_inicio} al {event.fecha_regreso}")

    location = event.nombre_lugar or event.lugar_salida or ""
    return build_google_calendar_url(title, start_date, end_date, parts, location)
