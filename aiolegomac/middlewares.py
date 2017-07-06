import jwt
from aiohttp import web


def json_error(message, status):
    return web.json_response({'error': message}, status=status)


async def error_middleware(app, handler):
    """Middleware that returns HTTP errors in json"""
    async def middleware_handler(request):
        try:
            response = await handler(request)
            if 400 <= response.status < 600:
                return json_error(response.reason, response.status)
            return response
        except web.HTTPException as ex:
            if 400 <= ex.status < 600:
                return json_error(ex.reason, ex.status)
            raise
    return middleware_handler


async def auth_middleware(app, handler):
    """Middleware that takes care of authentication

    If adds the user to the request if a valid token
    is sent in the header
    """
    async def middleware(request):
        request.user = None
        config = app['config']
        jwt_token = request.headers.get('authorization', None)
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, config['jwt_secret'],
                                     algorithms=[config['jwt_algorithm']])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                raise web.HTTPBadRequest(reason='Token is invalid')
            # We have only one user...
            if payload['user_id'] == 1:
                request.user = config['username']
        return await handler(request)
    return middleware


def setup_middlewares(app):
    app.middlewares.append(error_middleware)
    app.middlewares.append(auth_middleware)
