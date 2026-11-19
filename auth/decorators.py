from functools import wraps
from flask import abort, request


def login_required(view):
    @wraps(view)
    def protected(*args, **kwargs):
        if "unifica.account" not in request.environ:
            abort(401)
        return view(*args, **kwargs)
    return protected

