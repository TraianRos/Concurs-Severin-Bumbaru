from app.extensions import db
from app.models.entities import IncidentPhoto


class IncidentPhotoRepository:
    def create(
        self,
        *,
        incident_id: int,
        stored_name: str,
        original_name: str,
        mime_type: str,
        size_bytes: int,
        width: int,
        height: int,
        is_pertinent: bool = False,
    ) -> IncidentPhoto:
        photo = IncidentPhoto(
            incident_id=incident_id,
            stored_name=stored_name,
            original_name=original_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            width=width,
            height=height,
            is_pertinent=is_pertinent,
        )
        db.session.add(photo)
        db.session.flush()
        return photo

    def find_for_incident(self, photo_id: int, incident_id: int) -> IncidentPhoto | None:
        return IncidentPhoto.query.filter_by(id=photo_id, incident_id=incident_id).first()
