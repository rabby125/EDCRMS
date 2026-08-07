"""
Helper functions used when deleting a hierarchy node (Company, Data Center,
Building, Floor, or Room) that cascades down and removes every Rack and
Device underneath it.

Cable rows have a NOT NULL foreign key to devices, and Asset rows have a
nullable one. Neither is part of the SQLAlchemy cascade chain on Device, so
if we don't clean them up first, MySQL rejects the delete with a foreign
key constraint error partway through — even though the cascade looked like
it should "just work".

Call collect_device_ids_under_rooms() with every Room under the node being
deleted, then pass the result to detach_devices_before_delete() before
committing the delete.
"""
from typing import Iterable, List

from sqlalchemy.orm import Session

from app.models.cable_model import Cable
from app.models.asset_model import Asset


def collect_device_ids_under_rooms(rooms: Iterable) -> List[int]:
    device_ids = []
    for room in rooms:
        for rack in room.racks:
            for device in rack.devices:
                device_ids.append(device.id)
    return device_ids


def detach_devices_before_delete(db: Session, device_ids: List[int]):
    if not device_ids:
        return

    # Cables can't be nullified (NOT NULL FK), so they're removed outright —
    # deleting the whole hierarchy above them implies the cabling goes too.
    db.query(Cable).filter(
        (Cable.source_device_id.in_(device_ids)) | (Cable.dest_device_id.in_(device_ids))
    ).delete(synchronize_session=False)

    # Assets can be nullable-detached instead of deleted, so their history stays.
    db.query(Asset).filter(Asset.device_id.in_(device_ids)).update(
        {"device_id": None}, synchronize_session=False
    )