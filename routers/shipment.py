from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Form, Query
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from starlette.templating import Jinja2Templates

from api.dependencies import (
    ShipmentServiceDep,
    SellerDep,
    DeliveryPartnerDep,
    sessionDep,
)
from api.schemas.schema import (
    ShipmentRead,
    ShipmentCreate,
    ShipmentUpdate,
)
from config import app_settings
from core.exceptions import EntityNotFound
from database.models import TagName, Tag, Shipment, ShipmentTag
from utils.libs import TEMPLATE_DIR

router = APIRouter(
    prefix="/shipment",
    tags=["shipment"],
)

# Initialize Jinja2 environment once at module level
jinja_env = Environment(loader=FileSystemLoader("templates"))

templates = Jinja2Templates(TEMPLATE_DIR)


@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    shipment = await service.get(id)

    if shipment is None:
        raise EntityNotFound()

    return shipment


# tracking for a shipment
# response class is used to parse data to the response we want
# include_in_schema prevent the route fro showing in the docs
@router.get("/track", response_class=HTMLResponse, include_in_schema=False)
async def track_shipment(id: UUID, service: ShipmentServiceDep):
    template = jinja_env.get_template("track.html")

    # check for shipment with given id
    shipment = await service.get(id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given id does not exist"
        )

    # Compute status from timeline (latest event)
    current_status = (
        shipment.timeline[-1].status.value if shipment.timeline else "unknown"
    )
    context = shipment.model_dump()
    context["current_status"] = current_status
    context["partner"] = shipment.delivery_partner.name
    context["timeline"] = shipment.timeline

    return HTMLResponse(content=template.render(context))


@router.post(
    "/",
    response_model=ShipmentRead,
    name="Create a new shipment",
    status_code=status.HTTP_201_CREATED,
)
async def submit_shipment(
    seller: SellerDep,
    body: ShipmentCreate,
    service: ShipmentServiceDep,
):
    return await service.add(body, seller)


@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    body: ShipmentUpdate,
    service: ShipmentServiceDep,
    partner: DeliveryPartnerDep,
):
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


## get all shipment by a tag
@router.get("/tagged", response_model=list[ShipmentRead])
async def get_tagged_shipments(
    tag_name: TagName, session: sessionDep, service: ShipmentServiceDep
):
    # First check if tag exists
    tag = await session.scalar(select(Tag).where(Tag.name == tag_name.value))

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag '{tag_name.value}' not found in database",
        )

    # Query shipment IDs with this tag via the linking table
    result = await session.execute(
        select(Shipment.id)
        .join(ShipmentTag, Shipment.id == ShipmentTag.shipment_id)
        .join(Tag, Tag.id == ShipmentTag.tag_id)
        .where(Tag.name == tag_name.value)
    )

    shipment_ids = result.scalars().all()

    # Load each shipment with all relationships properly loaded using the service layer
    shipments = []
    for shipment_id in shipment_ids:
        shipment = await service.get(shipment_id)
        if shipment:
            shipments.append(shipment)

    return shipments


## Add a tag to shipment
@router.get("/tag", response_model=ShipmentRead)
async def add_tag_to_shipment(id: UUID, tag_name: TagName, service: ShipmentServiceDep):
    return await service.add_tag(id, tag_name)


## remove a tag to shipment
@router.delete("/tag", response_model=ShipmentRead)
async def remove_tag_from_shipment(
    id: UUID, tag_name: TagName, service: ShipmentServiceDep
):
    return await service.remove_tag(id, tag_name)


@router.delete("/")
async def delete_shipment(id: UUID, service: ShipmentServiceDep) -> dict[str, str]:
    await service.delete(id)
    return {"detail": f"Shipment #{id} deleted"}


# cancel shipment
@router.get("/cancel", response_model=ShipmentRead)
async def cancel_shipment(id: UUID, service: ShipmentServiceDep, seller: SellerDep):
    return await service.cancel(id, seller)


### display review form html page
@router.get("/review", response_class=HTMLResponse, response_model=None)
async def get_review_form(token: str = Query(...)):
    templates = jinja_env.get_template("review.html")
    content = templates.render(
        {
            "token": token,
            "review_url": f"http://{app_settings.APP_DOMAIN}/shipment/review?token={token}",
        }
    )

    return HTMLResponse(content)


### submit shipment review
@router.post("/review")
async def submit_review(
    service: ShipmentServiceDep,
    token: str = Query(...),
    rating: int = Form(ge=1, le=5),
    comment: str | None = Form(default=None),
):
    await service.rate(token, rating, comment)
    return {
        "detail": "Review submitted",
    }
