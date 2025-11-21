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


# enum check
@router.patch("/")
async def update_shipment(
    id: UUID,
    body: ShipmentUpdate,
    service: ShipmentServiceDep,
    partner: DeliveryPartnerDep,
) -> Shipment:
    update = body.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )

    shipment = await service.update(update, id)

    return shipment


@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    await service.delete(id)
    return {"detail": f"Shipment #{id} deleted"}
