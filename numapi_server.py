"""My attempt at numbersAPI."""
import urllib.parse as urlparse
from urllib.error import HTTPError
# Please remove or change proxy before running
from urllib.request import (
    ProxyHandler, build_opener, install_opener, urlopen
)

from flask import Flask, Response, jsonify

from marshmallow import Schema, ValidationError, validates_schema

from webargs import fields, validate
from webargs.flaskparser import abort, use_args


app = Flask(__name__)
# proxy_support = ProxyHandler({'http': 'http://192.168.0.3:8080'})
# opener = build_opener(proxy_support)
# install_opener(opener)


def is_int(x):
    """Check if string is int."""
    try:
        int(x)
    except Exception:
        return False
    return True


class AddrSchema(Schema):
    """For url parameters."""

    param0 = fields.String(
        validate=lambda x: is_int(x) or x == 'random', required=True
    )
    param1 = fields.String(
        validate=lambda x: is_int(x) or x in {'trivia', 'math', 'date', 'year'}
    )
    param2 = fields.String(validate=lambda x: x == 'date')

    @validates_schema
    def validate_interactions(self, data, **kwargs):
        """To check parameters combination."""
        if data['param0'] == 'random' and data.get('param2', None):
            raise ValidationError(f'Wrong parameter {data["param2"]}')
        if data['param0'] == 'random' and is_int(data.get('param1', None)):
            raise ValidationError(f'Wrong parameter {data["param1"]}')
        if data.get('param2', None) == 'date':
            if not is_int(data.get('param0', None)):
                raise ValidationError(f'{data["param0"]} should be Integer')
            if not is_int(data.get('param1', None)):
                raise ValidationError(f'{data["param1"]} should be Integer')


@app.errorhandler(422)
@app.errorhandler(ValidationError)
def handle_error(err):
    """Flask error handler."""
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), 422


@app.route('/')
def missed_the_point():
    """In case someone wants to try an empty path."""
    abort(422, messages={'_schema': ['Please, more parameters']})


@app.route('/<path:subpath>')
@use_args({
    'fragment': fields.String(validate=lambda x: x == ''),
    'notfound': fields.String(validate=validate.OneOf({'floor', 'ceil'})),
    'default': fields.String(),
    'min': fields.Integer(),
    'max': fields.Integer(),
}, location='query')
def api_main(args, subpath):
    """
    Ah yes, API.

    :param args: from use_args decorator
    :param subpath: from route
    :return: json from numbersAPI or error
    """
    # validating params from url
    params = {
        f'param{num}': val for num, val in enumerate(subpath.split('/'))
    }
    schema = AddrSchema()
    try:
        schema.load(params)
    except ValidationError as val_err:
        abort(422, messages=val_err.messages)

    url = f'http://numbersapi.com/{subpath}'
    # adding query to the url
    url_parts = list(urlparse.urlparse(url))
    url_parts[4] = urlparse.urlencode({'json': '', **args})
    # getting json response from numsApi
    try:
        resp = urlopen(urlparse.urlunparse(url_parts)).read()
        return Response(
            response=resp,
            mimetype='application/json',
        )
    except HTTPError as e:
        abort(422, messages={'_schema': [f'Wrong parameters\n{e}']})


if __name__ == '__main__':
    app.run(host="localhost", port=5000, threaded=True)
