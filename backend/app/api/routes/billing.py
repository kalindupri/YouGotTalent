from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.payments.base import PaymentGateway
from app.core.payments.factory import get_gateway
from app.crud import pricing as pricing_crud
from app.crud import subscription as subscription_crud
from app.crud.recruiter_profile import get_recruiter_profile_by_user
from app.crud.talent_profile import list_talent_profiles_by_user
from app.db.session import get_db
from app.models.recruiter_profile import RecruiterProfile
from app.models.talent_profile import TalentProfile
from app.models.user import User, UserRole
from app.schemas.pricing import CurrentPricing
from app.schemas.subscription import CancelRequest, CheckoutRequest, CheckoutResponse, PaymentRead, RetentionOfferRead, SubscriptionRead

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/pricing", response_model=CurrentPricing)
def read_current_pricing(db: Session = Depends(get_db)):
    return pricing_crud.current_prices(db)


def _current_profile(db: Session, user: User) -> TalentProfile | RecruiterProfile:
    if user.role == UserRole.TALENT:
        # A subscription belongs to one profile, so an account managing several children must
        # say which one it means. Refusing beats silently charging the wrong child's profile.
        # TODO: accept X-Talent-Profile-Id here once the dashboard has a profile switcher.
        profiles = list_talent_profiles_by_user(db, user.id)
        if len(profiles) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You manage more than one profile. Choose which one you're working on.",
            )
        profile = profiles[0] if profiles else None
    elif user.role == UserRole.RECRUITER:
        profile = get_recruiter_profile_by_user(db, user.id)
    else:
        profile = None
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create your profile before managing billing")
    return profile


@router.get("/me", response_model=SubscriptionRead | None)
def read_my_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _current_profile(db, user)
    if isinstance(profile, TalentProfile):
        sub = subscription_crud.get_for_talent(db, profile.id)
    else:
        sub = subscription_crud.get_for_recruiter(db, profile.id)
    if sub is not None:
        subscription_crud.sync_if_expired(db, sub)
    return sub


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def start_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    gateway: PaymentGateway = Depends(get_gateway),
):
    profile = _current_profile(db, user)
    return_url = f"{settings.FRONTEND_URL}/billing/success"
    kwargs = {"talent_profile": profile} if isinstance(profile, TalentProfile) else {"recruiter_profile": profile}
    _sub, checkout = subscription_crud.start_checkout(db, gateway, return_url, payload.billing_cycle, **kwargs)
    return CheckoutResponse(redirect_url=checkout.redirect_url, method=checkout.method, fields=checkout.fields)


def _current_subscription(db: Session, profile: TalentProfile | RecruiterProfile):
    sub = (
        subscription_crud.get_for_talent(db, profile.id)
        if isinstance(profile, TalentProfile)
        else subscription_crud.get_for_recruiter(db, profile.id)
    )
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found")
    return sub


@router.post("/cancel", response_model=SubscriptionRead)
def cancel_my_subscription(
    payload: CancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    gateway: PaymentGateway = Depends(get_gateway),
):
    profile = _current_profile(db, user)
    sub = _current_subscription(db, profile)
    return subscription_crud.request_cancellation(db, gateway, sub, payload.reason_category, payload.reason_detail)


@router.post("/reactivate", response_model=SubscriptionRead)
def reactivate_my_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _current_profile(db, user)
    sub = _current_subscription(db, profile)
    if not sub.cancel_at_period_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This subscription isn't scheduled to cancel")
    return subscription_crud.reactivate(db, sub)


@router.get("/retention-offer", response_model=RetentionOfferRead)
def read_retention_offer(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _current_profile(db, user)
    sub = _current_subscription(db, profile)
    return subscription_crud.retention_offer_status(sub)


@router.post("/retention-offer/accept", response_model=SubscriptionRead)
def accept_retention_offer(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _current_profile(db, user)
    sub = _current_subscription(db, profile)
    if sub.retention_offer_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This discount has already been used")
    return subscription_crud.accept_retention_offer(db, sub)


@router.get("/payments", response_model=list[PaymentRead])
def read_my_payments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _current_profile(db, user)
    sub = _current_subscription(db, profile)
    return subscription_crud.list_payments(db, sub.id)


@router.post("/webhook/payhere", include_in_schema=False)
async def payhere_webhook(request: Request, db: Session = Depends(get_db)):
    from app.core.payments.payhere import PayHereGateway

    payload = await request.body()
    event = PayHereGateway().verify_webhook(payload, dict(request.headers))
    if event is not None:
        subscription_crud.apply_webhook_event(db, event)
    return {"status": "ok"}


@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    from app.core.payments.stripe_gateway import StripeGateway

    payload = await request.body()
    event = StripeGateway().verify_webhook(payload, dict(request.headers))
    if event is not None:
        subscription_crud.apply_webhook_event(db, event)
    return {"status": "ok"}
