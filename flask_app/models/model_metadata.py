from marshmallow import fields

from flask_app.ext.schema import ma

_metadata_template = {

    "current_page": 0,
    "total_pages": 0,
    "total_items": 0,
    "items_per_page": 0,
    "Links": [
    ]

}


def build_metadata(page, page_size, total_pages, total_units, ENDPOINT):
    _metadata = _metadata_template.copy()
    if total_pages > 1:
        _metadata['Links'] = []

        if page < total_pages:
            next_link = page + 1
            _metadata['Links'].append(
                {"next": f"/api/v1/{ENDPOINT}?page={next_link}&page_size={page_size}"},
            )
        if page > 1:
            previous_link = page - 1
            _metadata['Links'].append(
                {"previous": f"/api/v1/{ENDPOINT}?page={previous_link}&page_size={page_size}"})
    else:
        _metadata.pop('Links')
    _metadata['current_page'] = page
    _metadata['items_per_page'] = page_size
    _metadata['total_pages'] = total_pages
    _metadata['total_items'] = total_units

    return _metadata


class MetadataSchema(ma.Schema):
    page = fields.Integer(required=True)
    page_count = fields.Integer(required=True)
    per_page = fields.Integer(required=True)
    total_count = fields.Integer(required=True)
    links = fields.List(fields.Dict(), required=True)
