from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


def _decimal(value):
    return Decimal(str(value or 0))


def motorcycle_route_is_eligible(total_distance_km, package_weight_kg, settings):
    """Valida a viagem completa, inclusive retorno, contra a capacidade cadastrada."""
    if not settings or not settings.motorcycle_enabled:
        return False
    if total_distance_km is None or total_distance_km < 0:
        return False
    if total_distance_km > settings.max_roundtrip_km:
        return False
    weight_limit = settings.max_package_weight_kg
    if weight_limit and package_weight_kg and package_weight_kg > weight_limit:
        return False
    return True


def motorcycle_quote_breakdown(total_distance_km, travel_minutes, settings):
    """Calcula o custo operacional; o preço comercial pode subsidiar parte dele."""
    if not motorcycle_route_is_eligible(total_distance_km, None, settings):
        return None

    distance = _decimal(total_distance_km)
    fuel_cost_per_km = Decimal("0")
    efficiency = _decimal(settings.fuel_efficiency_km_l)
    if efficiency > 0:
        fuel_cost_per_km = _decimal(settings.fuel_price_per_liter) / efficiency

    distance_cost = distance * (
        fuel_cost_per_km + _decimal(settings.maintenance_cost_per_km)
    )
    time_cost = (_decimal(travel_minutes) / Decimal("60")) * _decimal(
        settings.hourly_rate
    )
    operational_cost = (distance_cost + time_cost).quantize(
        MONEY, rounding=ROUND_HALF_UP
    )
    customer_fee = max(operational_cost, _decimal(settings.minimum_fee)).quantize(
        MONEY, rounding=ROUND_HALF_UP
    )

    return {
        "total_distance_km": float(distance),
        "fuel_cost_per_km": float(fuel_cost_per_km.quantize(MONEY)),
        "distance_cost": float(distance_cost.quantize(MONEY)),
        "time_cost": float(time_cost.quantize(MONEY)),
        "operational_cost": float(operational_cost),
        "suggested_customer_fee": float(customer_fee),
    }
