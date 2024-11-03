from blacksheep import Response

from exceptions import LogicalError

async def exception_handler_middleware(request, handler):
    try:
        response = await handler(request)
    except LogicalError as e:
        # todo: logging.
        print(e)
        return Response(500)
    return response

