class EntityNotFound(Exception):
    def __init__(self, entity: str, entity_id):
        super().__init__(f"{entity} introuvable")
        self.entity = entity
        self.entity_id = entity_id


class ReferenceNotFound(EntityNotFound):
    pass
