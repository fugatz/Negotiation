from __future__ import annotations

import json
import re
from functools import lru_cache

from .common import FIXTURE_DIR


def _slug(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _rounded_amount(value: float) -> int:
    step = 50 if value < 5000 else 100
    return int(round(value / step) * step)


@lru_cache(maxsize=1)
def _market_fixture() -> dict:
    with (FIXTURE_DIR / "market_cost_indexes.json").open() as handle:
        data = json.load(handle)
    data["recordsBySlug"] = {_slug(record["country"]): record for record in data["records"]}
    return data


@lru_cache(maxsize=1)
def _actor_rate_cards() -> list[dict]:
    with (FIXTURE_DIR / "actor_rate_cards.json").open() as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _paid_rate_actuals() -> list[dict]:
    path = FIXTURE_DIR / "paid_rate_actuals.json"
    if not path.exists():
        return []
    with path.open() as handle:
        return json.load(handle)


def _project_country_record(project: dict) -> dict | None:
    records_by_slug = _market_fixture()["recordsBySlug"]
    candidates = [
        project.get("shoot_country"),
        project.get("country"),
        project.get("production_country"),
        project.get("market"),
    ]
    for candidate in candidates:
        slug = _slug(candidate)
        if slug in records_by_slug:
            return records_by_slug[slug]
    return None


def _project_country_slug(project: dict) -> str:
    for candidate in [
        project.get("shoot_country"),
        project.get("country"),
        project.get("production_country"),
        project.get("market"),
    ]:
        slug = _slug(candidate)
        if slug:
            return slug
    return ""


def _matches_any(value: object, options: list[object] | None) -> bool:
    if not options:
        return True
    option_slugs = {_slug(option) for option in options}
    return "any" in option_slugs or _slug(value) in option_slugs


def actor_rate_card_context(project: dict) -> dict | None:
    if project.get("talent_class_scope") != "actor":
        return None

    country_slug = _project_country_slug(project)
    role = project.get("actor_role_scope")
    project_type = project.get("project_type")
    usage_scope = project.get("usage_scope")

    for card in _actor_rate_cards():
        applies_to = card.get("appliesTo", {})
        if _slug(card["country"]) != country_slug:
            continue
        if role and role not in set(applies_to.get("actorRoles", [])):
            continue
        if project_type and project_type not in set(applies_to.get("projectTypes", [])):
            continue
        if usage_scope and usage_scope not in set(applies_to.get("usageScopes", [])):
            continue

        standard_day = card["standardRates"]["standardDayContinuousWorkingDay"]
        return {
            "available": True,
            "id": card["id"],
            "country": card["country"],
            "market": card["market"],
            "agreement": card["agreement"],
            "sourceName": card["sourceName"],
            "sourceFileName": card.get("sourceFileName"),
            "sourcePath": card.get("sourcePath"),
            "sourceUrl": card["sourceUrl"],
            "standardRatesImageUrl": card["standardRatesImageUrl"],
            "supplementaryFeesImageUrl": card["supplementaryFeesImageUrl"],
            "mealTravelImageUrl": card["mealTravelImageUrl"],
            "effectiveFrom": card["effectiveFrom"],
            "effectiveThrough": card["effectiveThrough"],
            "currency": card["currency"],
            "standardDayTotalWithHolidayPay": float(standard_day["totalWithHolidayPay"]),
            "basicDailyRate": float(standard_day["basicDailyRate"]),
            "holidayPayOnBasicDailyRate": float(standard_day["holidayPayOnBasicDailyRate"]),
            "overtimePer30MinutesIncludingHolidayPay": float(
                standard_day["overtimePer30MinutesIncludingHolidayPay"]
            ),
            "supplementaryFeeCategoryCount": len(card.get("supplementaryFees", {})),
            "mealBreakPenaltyTypes": sorted(card.get("mealBreakPenalties", {}).keys()),
            "travelAllowanceTypes": sorted(card.get("travelAllowances", {}).keys()),
            "rateAuthority": "published_rate_card",
            "appliesAutomatically": True,
        }
    return None


def actor_paid_rate_actual_context(project: dict) -> dict | None:
    if project.get("talent_class_scope") != "actor":
        return None

    country_slug = _project_country_slug(project)
    role = project.get("actor_role_scope")
    project_type = project.get("project_type")
    usage_scope = project.get("usage_scope")
    usage_territory = project.get("usage_territory")
    usage_term = project.get("usage_term")

    for actual in _paid_rate_actuals():
        applies_to = actual.get("appliesTo", {})
        if _slug(actual["country"]) != country_slug:
            continue
        if not _matches_any(role, applies_to.get("actorRoles")):
            continue
        if not _matches_any(project_type, applies_to.get("projectTypes")):
            continue
        if not _matches_any(usage_scope, applies_to.get("usageScopes")):
            continue
        if not _matches_any(usage_territory, applies_to.get("usageTerritories")):
            continue
        if not _matches_any(usage_term, applies_to.get("usageTerms")):
            continue

        rates = actual["observedRates"]
        high_day_rate = float(rates["highDayRate"])
        buyout_multiplier = float(rates.get("buyoutMultiplier", _buyout_multiplier(project)))
        estimated_buyout = float(rates.get("buyout", high_day_rate * buyout_multiplier))
        one_shoot_day_total = float(rates.get("oneShootDayTotal", high_day_rate + estimated_buyout))

        return {
            "available": True,
            "id": actual["id"],
            "country": actual["country"],
            "market": actual.get("market"),
            "sourceName": actual["sourceName"],
            "sourceType": actual.get("sourceType", "manual_paid_rate_actual"),
            "observedYear": actual.get("observedYear"),
            "sampleSize": int(actual.get("sampleSize", 1)),
            "confidence": actual.get("confidence", "directional_paid_actual"),
            "currency": actual["currency"],
            "observedHighDayRate": _rounded_amount(high_day_rate),
            "observedBuyoutMultiplier": buyout_multiplier,
            "observedBuyout": _rounded_amount(estimated_buyout),
            "observedOneShootDayTotal": _rounded_amount(one_shoot_day_total),
            "basis": actual["basis"],
            "notes": list(actual.get("notes", [])),
            "rateAuthority": "talent_owned_rate_range",
            "calibrationAuthority": "paid_rate_actuals",
            "appliesAutomatically": False,
        }
    return None


def actor_agreement_floor(project: dict) -> dict | None:
    card = actor_rate_card_context(project)
    if not card:
        return None

    exact_amount = float(card["standardDayTotalWithHolidayPay"])
    return {
        "amount": int(round(exact_amount)),
        "exactAmount": round(exact_amount, 2),
        "currency": card["currency"],
        "source": card["agreement"],
        "sourceUrl": card["sourceUrl"],
        "basis": "published_actor_rate_card",
    }


def _buyout_multiplier(project: dict) -> float:
    usage_territory = str(project.get("usage_territory") or "").lower()
    usage_term = str(project.get("usage_term") or "").lower()
    usage_scope = str(project.get("usage_scope") or "").lower()

    if "global" in usage_territory or "global" in usage_scope:
        return 5.0
    if "pan_european" in usage_territory or "pan-european" in usage_territory:
        if "perpetuity" in usage_term:
            return 5.0
        if "24" in usage_term:
            return 4.0
        return 3.0
    if "national" in usage_scope:
        return 2.0
    if usage_scope in {"background", "internal"}:
        return 0.0
    return 1.5


def _rate_pressure(prior: float) -> str:
    if prior <= 0.55:
        return "materially_lower_than_baseline"
    if prior < 0.85:
        return "lower_than_baseline"
    if prior > 1.15:
        return "higher_than_baseline"
    return "near_baseline"


def _actor_market_rate_prior(
    project: dict,
    talent_cost_prior: float,
    paid_actual: dict | None = None,
    rate_card: dict | None = None,
) -> dict | None:
    if project.get("talent_class_scope") != "actor":
        return None

    role = project.get("actor_role_scope") or "featured"
    if paid_actual:
        return {
            "role": role,
            "sourceType": "paid_rate_actuals",
            "sourceName": paid_actual["sourceName"],
            "sourceId": paid_actual["id"],
            "sourceConfidence": paid_actual["confidence"],
            "sampleSize": paid_actual["sampleSize"],
            "observedYear": paid_actual["observedYear"],
            "referenceCountry": paid_actual["country"],
            "referenceCurrency": paid_actual["currency"],
            "estimatedLocalHighDayRate": paid_actual["observedHighDayRate"],
            "estimatedLocalHighDayRateCurrency": paid_actual["currency"],
            "buyoutMultiplier": paid_actual["observedBuyoutMultiplier"],
            "estimatedBuyout": paid_actual["observedBuyout"],
            "estimatedOneShootDayTotal": paid_actual["observedOneShootDayTotal"],
            "currencyHandling": "observed_local_currency_rate_no_fx_conversion",
            "basis": paid_actual["basis"],
            "calibrationAuthority": "paid_rate_actuals",
            "rateAuthority": "talent_owned_rate_range",
        }

    if rate_card:
        session_day = round(float(rate_card["standardDayTotalWithHolidayPay"]), 2)
        return {
            "role": role,
            "sourceType": "published_rate_card",
            "sourceAgreement": rate_card["agreement"],
            "sourceUrl": rate_card["sourceUrl"],
            "referenceCountry": rate_card["country"],
            "referenceCurrency": rate_card["currency"],
            "estimatedLocalHighDayRate": session_day,
            "estimatedLocalHighDayRateCurrency": rate_card["currency"],
            "buyoutMultiplier": 0.0,
            "estimatedBuyout": 0.0,
            "estimatedOneShootDayTotal": session_day,
            "currencyHandling": "published_local_currency_rate",
            "basis": "published PACT/FAA standard day plus holiday pay",
            "calibrationAuthority": "published_rate_card",
            "rateAuthority": "talent_owned_rate_range",
        }

    reference = _market_fixture().get("actorReferenceRates", {}).get(role)
    if not reference:
        return None

    session_day = _rounded_amount(float(reference["referenceHighDayRate"]) * talent_cost_prior)
    buyout_multiplier = _buyout_multiplier(project)
    estimated_buyout = _rounded_amount(session_day * buyout_multiplier) if buyout_multiplier else 0

    return {
        "role": role,
        "sourceType": "cost_of_living_prior",
        "referenceCountry": reference["referenceCountry"],
        "referenceHighDayRate": int(reference["referenceHighDayRate"]),
        "referenceCurrency": reference["currency"],
        "estimatedLocalHighDayRate": session_day,
        "estimatedLocalHighDayRateCurrency": reference["currency"],
        "buyoutMultiplier": buyout_multiplier,
        "estimatedBuyout": estimated_buyout,
        "estimatedOneShootDayTotal": session_day + estimated_buyout,
        "currencyHandling": "relative_index_only_no_fx_conversion",
        "basis": reference["basis"],
        "calibrationAuthority": "advisory_prior",
        "rateAuthority": "talent_owned_rate_range",
    }


def market_cost_context(project: dict) -> dict:
    fixture = _market_fixture()
    baseline = fixture["recordsBySlug"][_slug(fixture["baselineCountry"])]
    record = _project_country_record(project)

    if not record:
        return {
            "available": False,
            "source": fixture["source"],
            "basis": fixture["basis"],
            "confidence": fixture["confidence"],
            "appliesAutomatically": False,
            "country": project.get("shoot_country") or project.get("market", "unknown_market"),
            "baselineCountry": baseline["country"],
        }

    cost_relative = float(record["costOfLivingIndex"]) / float(baseline["costOfLivingIndex"])
    purchasing_relative = float(record["localPurchasingPowerIndex"]) / float(baseline["localPurchasingPowerIndex"])
    talent_cost_prior = max(0.25, min(cost_relative * purchasing_relative, 1.6))
    paid_actual = actor_paid_rate_actual_context(project)
    rate_card = actor_rate_card_context(project)
    actor_market_prior = _actor_market_rate_prior(project, talent_cost_prior, paid_actual, rate_card)
    source_type = actor_market_prior.get("sourceType") if actor_market_prior else None
    prior_needs_review = source_type == "cost_of_living_prior"

    return {
        "available": True,
        "source": fixture["source"],
        "sourceFileName": fixture["sourceFileName"],
        "basis": fixture["basis"],
        "confidence": "paid_rate_actuals_available" if paid_actual else fixture["confidence"],
        "appliesAutomatically": bool(fixture["appliesAutomatically"]),
        "actualsOverride": fixture["actualsOverride"],
        "country": record["country"],
        "baselineCountry": baseline["country"],
        "rank": int(record["rank"]),
        "costOfLivingIndex": float(record["costOfLivingIndex"]),
        "rentIndex": float(record["rentIndex"]),
        "costOfLivingPlusRentIndex": float(record["costOfLivingPlusRentIndex"]),
        "localPurchasingPowerIndex": float(record["localPurchasingPowerIndex"]),
        "costOfLivingRelativeToBaseline": round(cost_relative, 3),
        "localPurchasingPowerRelativeToBaseline": round(purchasing_relative, 3),
        "talentCostPriorVsBaseline": round(talent_cost_prior, 3),
        "localBudgetLeverageVsBaseline": round(1.0 / talent_cost_prior, 3),
        "expectedLocalRatePressure": _rate_pressure(talent_cost_prior),
        "adminReviewRequired": prior_needs_review,
        "rateSourcePriority": "paid_rate_actuals_before_published_actor_rate_card_before_cost_prior",
        "paidRateActual": paid_actual,
        "actorRateCard": rate_card,
        "actorMarketRatePrior": actor_market_prior,
    }
