from database.models import ShipmentEvent, Shipment, ShipmentStatus
from services.base import BaseService


class ShipmentEventService(BaseService):
    def __init__(self, session):
        super().__init__(ShipmentEvent, session)

    async def add(
        self,
        shipment: Shipment,
        location: int | None = None,
        status: ShipmentStatus | None = None,
        description: str = None,
    ) -> ShipmentEvent:
        if not location:
            last_event = await self.get_latest_event(shipment)
            location = last_event.location

        if not status:
            last_event = await self.get_latest_event(shipment)
            status = last_event.status

        if not description:
            description = self._generate_description(status, location)

        new_event = ShipmentEvent(
            location=location,
            status=status,
            description=description,
            shipment_id=shipment.id,
        )

        return await self._add(new_event)

    async def get_latest_event(self, shipment: Shipment):
        timeline = shipment.timeline
        timeline.sort(key=lambda event: event.created_at, reverse=True)
        return timeline[0]

    def _generate_description(self, status: ShipmentStatus, location: int):
        match status:
            case ShipmentStatus.placed:
                return "assign delivery partner"
            case ShipmentStatus.out_for_delivery:
                return "shipment out for delivery"
            case ShipmentStatus.delivered:
                return "shipment delivered"
            case _:  # and include shipmentstatus.in_transit
                return f"scanned at {location}"
