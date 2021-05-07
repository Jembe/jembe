from werkzeug import exceptions as we


class JembeError(Exception):
    pass


class BadRequest(we.BadRequest):
    pass


class Unauthorized(we.Unauthorized):
    pass


class Forbidden(we.Forbidden):
    pass


class NotFound(we.NotFound):
    pass


class AccessDenied(NotFound):
    pass


class Conflict(we.Conflict):
    pass


class Gone(we.Gone):
    pass


class InternalServerError(we.InternalServerError):
    pass


class NotImplemented(we.NotImplemented):
    pass
