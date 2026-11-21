from repositories.design_image_repository import delete_design_images
from repositories.design_repository import delete_design_record, get_design


def delete_catalog_design(design_id: int) -> None:
    if not get_design(design_id):
        raise ValueError("El diseño que intentas eliminar ya no existe.")
    delete_design_images(design_id)
    delete_design_record(design_id)
