from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.catalog.models import Design, GarmentFamily, ShopDesignPrice
from apps.tenants.currency import normalize_currency
from apps.tenants.models import MembershipWorkFunction, ShopRole, Tenant, TenantMember
from apps.works.constants import NEXT_STATUS, STAGE_FUNCTION, WorkStatus
from apps.works.models import WorkEvent, WorkOrder


class WorkConflict(APIException):
    status_code = 409
    default_detail = "Work changed since it was loaded. Refresh and try again."
    default_code = "stale_work"


def has_function(membership, code):
    return bool(
        membership
        and MembershipWorkFunction.objects.filter(
            membership=membership,
            function_code=code,
            deleted__isnull=True,
        ).exists()
    )


def can_create(context):
    member = context.membership
    return bool(
        member
        and (
            member.role == ShopRole.ADMIN
            or (
                member.role == ShopRole.STAFF
                and (
                    has_function(member, "SALES") or has_function(member, "MEASUREMENT")
                )
            )
        )
    )


def require_admin(context):
    if not context.membership or context.membership.role != ShopRole.ADMIN:
        raise PermissionDenied("Shop ADMIN role required.")


def _lock_current_member(*, context, actor):
    member = context.membership
    if not member:
        raise PermissionDenied("Active Shop operator required.")
    try:
        return TenantMember.objects.select_for_update().select_related("user").get(
            pk=member.pk,
            tenant=context.shop,
            user=actor,
            is_active=True,
            user__is_active=True,
            deleted__isnull=True,
        )
    except TenantMember.DoesNotExist as error:
        raise PermissionDenied("Active Shop operator required.") from error


def _work_state(order):
    """Store stable identifiers and workflow fields, never customer notes."""
    return {
        "work_number": order.work_number,
        "client_id": str(order.client_id),
        "related_person_id": str(order.related_person_id) if order.related_person_id else None,
        "design_version_id": str(order.design_version_id),
        "design_price_amount": (
            str(order.design_price_amount) if order.design_price_amount is not None else None
        ),
        "design_price_currency": order.design_price_currency,
        "measurement_set_id": str(order.measurement_set_id),
        "material_id": str(order.material_id) if order.material_id else None,
        "assigned_membership_id": (
            str(order.assigned_membership_id) if order.assigned_membership_id else None
        ),
        "status": order.status,
        "priority": order.priority,
        "due_date": order.due_date.isoformat() if order.due_date else None,
    }


def _record_event(*, order, actor, action, before_state, after_state, changed_fields):
    WorkEvent.objects.create(
        tenant_id=order.tenant_id,
        work=order,
        actor_id=actor.pk,
        action=action,
        before_state=before_state,
        after_state=after_state,
        changed_fields=sorted(set(changed_fields)),
    )


def due_indicator(order, *, now=None):
    if order.due_date is None:
        return None
    try:
        zone = ZoneInfo(order.tenant.default_timezone or settings.TIME_ZONE)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo(settings.TIME_ZONE)
    today = timezone.localtime(now or timezone.now(), zone).date()
    if order.due_date < today:
        return "OVERDUE"
    if order.due_date == today:
        return "DUE_TODAY"
    if order.due_date <= today + timedelta(days=2):
        return "DUE_SOON"
    return "UPCOMING"


@transaction.atomic
def create_work(*, context, actor, values):
    Tenant.objects.select_for_update().get(pk=context.shop.pk)
    member = _lock_current_member(context=context, actor=actor)
    if not (
        member.role == ShopRole.ADMIN
        or (
            member.role == ShopRole.STAFF
            and (
                has_function(member, "SALES") or has_function(member, "MEASUREMENT")
            )
        )
    ):
        raise PermissionDenied(
            "Work creation requires ADMIN or SALES/MEASUREMENT STAFF."
        )
    design_id = values["design_version"].design_id
    family_id = Design.objects.values_list("family_id", flat=True).get(pk=design_id)
    # Keep Shop → Family → Design locking: Shop/Design archival and Family
    # archival must not race the authoritative WorkOrder.clean() check.
    GarmentFamily.all_objects.select_for_update().only("pk").get(pk=family_id)
    Design.objects.select_for_update().only("pk").get(
        pk=design_id, family_id=family_id
    )
    design_price = (
        ShopDesignPrice.objects.select_for_update()
        .filter(tenant=context.shop, design_id=design_id)
        .first()
    )
    if design_price:
        try:
            shop_currency = normalize_currency(context.shop.default_currency)
        except ValueError:
            raise ValidationError(
                {"design_version": "Set a valid Shop default currency before using its Design price."}
            ) from None
        if design_price.currency != shop_currency:
            raise ValidationError(
                {"design_version": "Update this Design price to match the Shop currency before creating Work."}
            )
    sequence = (
        WorkOrder.all_objects.filter(tenant=context.shop).aggregate(
            maximum=Max("sequence")
        )["maximum"]
        or 0
    ) + 1
    order = WorkOrder(
        tenant=context.shop,
        sequence=sequence,
        work_number=f"ORD-{sequence:06d}",
        created_by=actor,
        updated_by=actor,
        design_price_amount=design_price.amount if design_price else None,
        design_price_currency=design_price.currency if design_price else None,
        **values,
    )
    try:
        order.save()
    except DjangoValidationError as error:
        raise ValidationError(
            error.message_dict if hasattr(error, "message_dict") else error.messages
        ) from error
    _record_event(
        order=order,
        actor=actor,
        action=WorkEvent.Action.CREATED,
        before_state={},
        after_state=_work_state(order),
        changed_fields=_work_state(order).keys(),
    )
    return order


@transaction.atomic
def update_work(*, context, actor, order_id, values):
    order = WorkOrder.objects.select_for_update().get(pk=order_id, tenant=context.shop)
    member = _lock_current_member(context=context, actor=actor)
    if member.role != ShopRole.ADMIN:
        raise PermissionDenied("Shop ADMIN role required.")
    if order.status == WorkStatus.COMPLETED:
        raise ValidationError("Completed Work cannot be edited.")
    before_state = _work_state(order)
    for field, value in values.items():
        setattr(order, field, value)
    order.updated_by = actor
    try:
        order.save(update_fields=[*values, "updated_by", "updated_at"])
    except DjangoValidationError as error:
        raise ValidationError(
            error.message_dict if hasattr(error, "message_dict") else error.messages
        ) from error
    _record_event(
        order=order,
        actor=actor,
        action=WorkEvent.Action.UPDATED,
        before_state=before_state,
        after_state=_work_state(order),
        changed_fields=values.keys(),
    )
    return order


@transaction.atomic
def assign_work(*, context, actor, order_id, membership):
    order = WorkOrder.objects.select_for_update().get(pk=order_id, tenant=context.shop)
    actor_member = _lock_current_member(context=context, actor=actor)
    if actor_member.role != ShopRole.ADMIN:
        raise PermissionDenied("Shop ADMIN role required.")
    if order.status == WorkStatus.COMPLETED:
        raise ValidationError("Completed Work cannot be assigned.")
    if membership is not None:
        try:
            membership = TenantMember.objects.select_for_update().select_related(
                "user"
            ).get(
                pk=membership.pk,
                tenant=context.shop,
                is_active=True,
                user__is_active=True,
                deleted__isnull=True,
            )
        except TenantMember.DoesNotExist as error:
            raise ValidationError(
                {"membership_id": "Active member in this Shop required."}
            ) from error
        needed = STAGE_FUNCTION.get(order.status)
        if needed and not has_function(membership, needed):
            raise ValidationError(
                {"membership_id": "Member lacks the current stage function."}
            )
        if order.status == WorkStatus.REQUEST and not (
            has_function(membership, "SALES") or has_function(membership, "MEASUREMENT")
        ):
            raise ValidationError(
                {"membership_id": "Request requires SALES or MEASUREMENT."}
            )
    before_state = _work_state(order)
    order.assigned_membership = membership
    order.updated_by = actor
    order.save(update_fields=["assigned_membership", "updated_by", "updated_at"])
    _record_event(
        order=order,
        actor=actor,
        action=WorkEvent.Action.ASSIGNED,
        before_state=before_state,
        after_state=_work_state(order),
        changed_fields=("assigned_membership_id",),
    )
    return order


@transaction.atomic
def advance_work(*, context, actor, order_id, expected_status):
    order = WorkOrder.objects.select_for_update().get(pk=order_id, tenant=context.shop)
    member = _lock_current_member(context=context, actor=actor)
    if not member or member.role not in (ShopRole.ADMIN, ShopRole.STAFF):
        raise PermissionDenied("Active Shop operator required.")
    if order.status != expected_status:
        raise WorkConflict()
    destination = NEXT_STATUS.get(order.status)
    if destination is None:
        raise ValidationError("Completed Work has no next stage.")
    if order.assigned_membership_id and order.assigned_membership_id != member.pk:
        raise PermissionDenied("Work is assigned to another member.")
    needed = STAGE_FUNCTION.get(order.status)
    if needed and not has_function(member, needed):
        raise PermissionDenied("Current stage Work Function required.")
    if order.status == WorkStatus.REQUEST and not (
        has_function(member, "SALES") or has_function(member, "MEASUREMENT")
    ):
        raise PermissionDenied("SALES or MEASUREMENT function required.")
    before_state = _work_state(order)
    order.status = destination
    order.assigned_membership = None
    order.updated_by = actor
    order.save(
        update_fields=["status", "assigned_membership", "updated_by", "updated_at"]
    )
    _record_event(
        order=order,
        actor=actor,
        action=WorkEvent.Action.STAGE_TRANSITIONED,
        before_state=before_state,
        after_state=_work_state(order),
        changed_fields=("status", "assigned_membership_id"),
    )
    return order


@transaction.atomic
def delete_work(*, context, actor, order_id):
    order = WorkOrder.objects.select_for_update().get(pk=order_id, tenant=context.shop)
    member = _lock_current_member(context=context, actor=actor)
    if member.role != ShopRole.ADMIN:
        raise PermissionDenied("Shop ADMIN role required.")
    if order.status != WorkStatus.REQUEST:
        raise ValidationError("Only Request-stage Work can be removed.")
    if order.invoices.exists():
        raise ValidationError("Work with billing records cannot be removed.")
    before_state = _work_state(order)
    order.updated_by = actor
    order.save(update_fields=["updated_by", "updated_at"])
    order.delete()
    _record_event(
        order=order,
        actor=actor,
        action=WorkEvent.Action.SOFT_DELETED,
        before_state=before_state,
        after_state={"deleted_at": order.deleted.isoformat() if order.deleted else None},
        changed_fields=("deleted",),
    )
