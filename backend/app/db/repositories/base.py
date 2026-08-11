from bson import ObjectId


def serialize_doc(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    result = dict(doc)
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return result


def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)
