from fastapi import FastAPI, Request, Response, HTTPException, status


class FastShipError(Exception):
    """
    Base exception for Fastship api
    """

    status = status.HTTP_400_BAD_REQUEST


class EntityNotFound(FastShipError):
    """
    Entity not found in database
    """

    status = status.HTTP_404_NOT_FOUND


class ClientNotAuthorized(FastShipError):
    """
    Client is not authorized to perform the action
    """

    status = status.HTTP_401_UNAUTHORIZED


class BadCredentials(FastShipError):
    """
    User email or password is incorrect
    """

    status = status.HTTP_401_UNAUTHORIZED


class InvalidToken(FastShipError):
    """
    Access token is invalid or expired
    """

    status = status.HTTP_401_UNAUTHORIZED


class DeliveryPartnerCapacityExceeded(FastShipError):
    """
    Delivery partner has reached their max handling capacity
    """

    status = status.HTTP_406_NOT_ACCEPTABLE


def _get_handler(status: int, detail: str):
    def handler(request: Request, exception: Exception) -> Response:
        raise HTTPException(status_code=status, detail=detail)

    return handler


def add_exception_handlers(app: FastAPI):
    for subclass in FastShipError.__subclasses__():
        app.add_exception_handler(
            subclass, _get_handler(subclass.status, subclass.__doc__)
        )
