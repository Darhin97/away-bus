from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from api.dependencies import ShipmentServiceDep, SellerDep, DeliveryPartnerDep
from api.schemas.schema import ShipmentRead, ShipmentCreate, ShipmentUpdate
from database.models import Shipment


router = APIRouter(
    prefix="/shipment",
    tags=["shipment"],
)


@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, _: SellerDep, service: ShipmentServiceDep):
    shipment = await service.get(id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given id does not exist"
        )

    return shipment


@router.post("/")
async def submit_shipment(
    seller: SellerDep,
    body: ShipmentCreate,
    service: ShipmentServiceDep,
) -> Shipment:
    return await service.add(body, seller)


@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    body: ShipmentUpdate,
    service: ShipmentServiceDep,
    partner: DeliveryPartnerDep,
) -> Shipment:
    """
    Update a shipment's status, location, or estimated delivery.

    **Authentication Required**: You must be logged in as a delivery partner.
    - Use the `/partner/login` endpoint to get an access token
    - Only the delivery partner assigned to this shipment can update it

    **Updatable Fields**:
    - `status`: Update shipment status (in_transit, out_for_delivery, delivered, etc.)
    - `location`: Update current location (zip code)
    - `estimated_delivery`: Update estimated delivery date/time
    - `description`: Custom description for the shipment event

    **Authorization**: Returns 401 Unauthorized if the logged-in partner is not assigned to this shipment.
    """
    update = body.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )

    shipment = await service.update(update, id, partner)

    return shipment


@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    await service.delete(id)
    return {"detail": f"Shipment #{id} deleted"}


# cancel shipment
@router.get("/cancel", response_model=ShipmentRead)
async def cancel_shipment(id: UUID, service: ShipmentServiceDep, seller: SellerDep):
    return await service.cancel(id, seller)
