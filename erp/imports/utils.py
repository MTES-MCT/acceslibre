def get_address_query_to_geocode(obj):
    parts = [
        obj.get("numero") or "",
        obj.get("voie") or "",
    ]
    city = " ".join([p for p in parts if p != ""]).strip()
    address_parts = [
        city,
        obj.get("lieu_dit") or "",
        obj.get("commune") or "",
    ]
    return ", ".join([p for p in address_parts if p != ""])
