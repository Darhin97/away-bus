from database.models import (
    ShipmentEvent,
    Shipment,
    ShipmentStatus,
    Seller,
    DeliveryPartner,
)
from services.base import BaseService
from services.notification import NotificationService
from sqlmodel import select


class ShipmentEventService(BaseService):
    def __init__(self, session, tasks):
        super().__init__(ShipmentEvent, session)
        self.notification_service = NotificationService(tasks)

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

        # Load seller and delivery_partner separately for notifications
        seller = await self.session.get(Seller, shipment.seller_id)
        delivery_partner = await self.session.get(
            DeliveryPartner, shipment.delivery_partner_id
        )

        await self._notify(shipment, seller, delivery_partner, status)

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
            case ShipmentStatus.cancelled:
                return "shipment cancelled by the seller"
            case _:  # and include shipmentstatus.in_transit
                return f"scanned at {location}"

    async def _notify(
        self,
        shipment: Shipment,
        seller: Seller,
        delivery_partner: DeliveryPartner,
        status: ShipmentStatus,
    ):
        if status == ShipmentStatus.in_transit:
            return

        subject: str
        context: dict = {}
        template_name: str

        match status:
            case ShipmentStatus.placed:
                subject = "Your Order is Shipped 🚛"
                context["seller"] = seller.name
                context["partner"] = delivery_partner.name
                template_name = "mail_placed.html"

            case ShipmentStatus.out_for_delivery:
                subject = "Your Order is Arriving Soon 🛵"
                template_name = "mail_out_for_delivery.html"

            case ShipmentStatus.delivered:
                subject = "Your Order is Delivered ✅"
                context["seller"] = shipment.seller.name
                template_name = "mail_delivered.html"

            case ShipmentStatus.cancelled:
                subject = "Your Order is Cancelled ❌"
                template_name = "mail_cancelled.html"

        await self.notification_service.send_template_email(
            recipients=[shipment.client_contact_email],
            subject=subject,
            context=context,
            template_name=template_name,
        )
