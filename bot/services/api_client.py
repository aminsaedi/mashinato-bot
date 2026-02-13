"""Async HTTP client for car-api-py - covers all API endpoints."""

from __future__ import annotations

import contextlib
import logging
import uuid
from typing import Any

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class CarAPI:
    """Async client for car-api-py REST API."""

    def __init__(self, access_token: str):
        self._token = access_token
        self._base = settings.api_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict | None = None,
    ) -> Any:
        url = f"{self._base}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
            )
        if resp.status_code == 204:
            return None
        if resp.status_code >= 400:
            detail = resp.text
            with contextlib.suppress(Exception):
                detail = resp.json().get("detail", detail)
            raise APIError(resp.status_code, str(detail))
        if not resp.content:
            return None
        return resp.json()

    async def _get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs) -> Any:
        return await self._request("POST", path, **kwargs)

    async def _put(self, path: str, **kwargs) -> Any:
        return await self._request("PUT", path, **kwargs)

    async def _patch(self, path: str, **kwargs) -> Any:
        return await self._request("PATCH", path, **kwargs)

    async def _delete(self, path: str, **kwargs) -> Any:
        return await self._request("DELETE", path, **kwargs)

    # ── Accounts ──────────────────────────────────────────────────────

    async def get_me(self) -> dict:
        return await self._get("/api/v1/accounts/me")

    async def get_account_status(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/status")

    async def get_next_free_time(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/next-free-time")

    # ── Search ────────────────────────────────────────────────────────

    async def start_search(self, account: str, params: dict) -> dict:
        return await self._post(f"/api/v1/accounts/{account}/searches", json=params)

    async def get_search_status(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/searches/current")

    async def stop_search(self, account: str) -> dict:
        return await self._delete(f"/api/v1/accounts/{account}/searches/current")

    async def get_search_filters(self) -> dict:
        return await self._get("/api/v1/search/filters")

    async def get_poll_intervals(self) -> dict:
        return await self._get("/api/v1/search/poll-intervals")

    async def update_poll_intervals(self, params: dict) -> dict:
        return await self._put("/api/v1/search/poll-intervals", json=params)

    # ── Optimization ──────────────────────────────────────────────────

    async def start_optimization(self, account: str, params: dict) -> dict:
        return await self._post(f"/api/v1/accounts/{account}/searches/optimize", json=params)

    async def get_optimization_status(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/searches/optimize/current")

    async def stop_optimization(self, account: str) -> dict:
        return await self._delete(f"/api/v1/accounts/{account}/searches/optimize/current")

    # ── Rentals ───────────────────────────────────────────────────────

    async def get_current_rental(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/rentals/current")

    async def book_car(self, account: str, vehicle_id: int) -> dict:
        return await self._post(
            f"/api/v1/accounts/{account}/rentals",
            json={"vehicle_id": vehicle_id},
        )

    async def extend_rental(self, account: str) -> dict:
        return await self._patch(f"/api/v1/accounts/{account}/rentals/current")

    async def cancel_rental(self, account: str) -> dict:
        return await self._delete(f"/api/v1/accounts/{account}/rentals/current")

    async def start_trip(self, account: str) -> dict:
        return await self._post(f"/api/v1/accounts/{account}/rentals/current/start")

    async def end_trip(self, account: str, move_to_another: bool = False) -> dict:
        params = None
        if move_to_another:
            params = {"move_to_another_account": "true"}
        return await self._post(
            f"/api/v1/accounts/{account}/rentals/current/end",
            params=params,
        )

    async def get_fuel_card(self, account: str) -> dict:
        return await self._get(f"/api/v1/accounts/{account}/rentals/current/fuel-card")

    # ── Transfer & Continue ───────────────────────────────────────────

    async def transfer_rental(self, from_account: str, to_account: str) -> dict:
        return await self._post(
            "/api/v1/transfer",
            json={"from_account": from_account, "to_account": to_account},
        )

    async def continue_rental(self, end_on: str, continue_on: str) -> dict:
        return await self._post(
            "/api/v1/continue",
            json={"end_on_account": end_on, "continue_on_account": continue_on},
        )

    # ── Vehicles ──────────────────────────────────────────────────────

    async def list_vehicles(self) -> dict:
        return await self._get("/api/v1/vehicles")

    async def get_vehicle(self, vehicle_id: int) -> dict:
        return await self._get(f"/api/v1/vehicles/{vehicle_id}")

    # ── Webhooks ──────────────────────────────────────────────────────

    async def list_webhook_events(self) -> dict:
        return await self._get("/api/v1/webhooks/events")

    async def list_webhooks(self, skip: int = 0, limit: int = 50) -> dict:
        return await self._get("/api/v1/webhooks", params={"skip": skip, "limit": limit})

    async def create_webhook(self, data: dict) -> dict:
        return await self._post("/api/v1/webhooks", json=data)

    async def get_webhook(self, webhook_id: int) -> dict:
        return await self._get(f"/api/v1/webhooks/{webhook_id}")

    async def update_webhook(self, webhook_id: int, data: dict) -> dict:
        return await self._put(f"/api/v1/webhooks/{webhook_id}", json=data)

    async def delete_webhook(self, webhook_id: int) -> None:
        await self._delete(f"/api/v1/webhooks/{webhook_id}")

    async def toggle_webhook(self, webhook_id: int) -> dict:
        return await self._patch(f"/api/v1/webhooks/{webhook_id}/toggle")

    async def test_webhook(self, webhook_id: int, event_type: str = "webhook.test") -> dict:
        return await self._post(
            f"/api/v1/webhooks/{webhook_id}/test",
            json={"event_type": event_type},
        )

    async def list_webhook_deliveries(
        self, webhook_id: int, skip: int = 0, limit: int = 20
    ) -> dict:
        return await self._get(
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            params={"skip": skip, "limit": limit},
        )

    async def get_webhook_delivery(self, delivery_id: int) -> dict:
        return await self._get(f"/api/v1/webhooks/deliveries/{delivery_id}")

    # ── Audit ─────────────────────────────────────────────────────────

    async def list_audit_logs(
        self,
        *,
        user_account: str | None = None,
        action: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        status_code: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if user_account:
            params["user_account"] = user_account
        if action:
            params["action"] = action
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if status_code is not None:
            params["status_code"] = status_code
        return await self._get("/api/v1/audit/logs", params=params)

    async def get_audit_log(self, log_id: int) -> dict:
        return await self._get(f"/api/v1/audit/logs/{log_id}")

    # ── Account Policies ──────────────────────────────────────────────

    async def list_policies(self) -> dict:
        return await self._get("/api/v1/policies")

    async def list_valid_actions(self) -> list:
        return await self._get("/api/v1/policies/actions")

    async def set_account_policies(self, account: str, denied_actions: list[str]) -> dict:
        return await self._put(
            f"/api/v1/policies/{account}",
            json={"denied_actions": denied_actions},
        )

    async def delete_account_policies(self, account: str) -> None:
        await self._delete(f"/api/v1/policies/{account}")

    # ── Subscriptions ─────────────────────────────────────────────────

    async def list_subscriptions(self) -> dict:
        return await self._get("/api/v1/subscriptions")

    async def set_subscription(self, account: str, has_subscription: bool) -> dict:
        return await self._put(
            f"/api/v1/subscriptions/{account}",
            json={"has_subscription": has_subscription},
        )

    async def delete_subscription(self, account: str) -> None:
        await self._delete(f"/api/v1/subscriptions/{account}")

    # ── Common ────────────────────────────────────────────────────────

    async def get_accessories(self) -> list:
        return await self._get("/api/v1/accessories")

    async def get_vehicle_models(self) -> list:
        return await self._get("/api/v1/vehicle-models")

    async def get_zones(self) -> dict:
        return await self._get("/api/v1/zones")

    # ── Health & Version ──────────────────────────────────────────────

    async def health_live(self) -> dict:
        return await self._get("/api/v1/health/live")

    async def health_ready(self) -> dict:
        return await self._get("/api/v1/health/ready")

    async def health_detail(self) -> dict:
        return await self._get("/api/v1/health/detail")

    async def get_version(self) -> dict:
        return await self._get("/api/v1/version")

    # ── Dispatcher (Admin) ────────────────────────────────────────────

    async def get_pool_status(self) -> dict:
        return await self._get("/api/v1/dispatcher/pool/status")

    async def list_agents(self) -> dict:
        return await self._get("/api/v1/dispatcher/agents")

    async def get_dispatcher_health(self) -> dict:
        return await self._get("/api/v1/dispatcher/health")

    # ── Droplets (Admin) ──────────────────────────────────────────────

    async def list_droplets(
        self, droplet_type: str | None = None, status: str | None = None
    ) -> list:
        params: dict[str, str] = {}
        if droplet_type:
            params["type"] = droplet_type
        if status:
            params["status"] = status
        return await self._get("/api/v1/droplets/", params=params or None)

    async def register_droplet(self, data: dict) -> dict:
        return await self._post("/api/v1/droplets/register", json=data)

    async def get_droplet(self, droplet_id: int) -> dict:
        return await self._get(f"/api/v1/droplets/{droplet_id}")

    async def delete_droplet(self, droplet_id: int) -> dict:
        return await self._delete(f"/api/v1/droplets/{droplet_id}")

    async def get_droplets_summary(self) -> dict:
        return await self._get("/api/v1/droplets/summary/stats")

    # ── IPv6 Pool (Admin) ─────────────────────────────────────────────

    async def list_ipv6_addresses(self, status: str | None = None) -> list:
        params = {"status": status} if status else None
        return await self._get("/api/v1/ipv6-pool/addresses", params=params)

    async def block_ipv6(self, address: str, reason: str | None = None) -> dict:
        json_data = {"reason": reason} if reason else None
        return await self._post(f"/api/v1/ipv6-pool/addresses/{address}/block", json=json_data)

    async def unblock_ipv6(self, address: str) -> dict:
        return await self._post(f"/api/v1/ipv6-pool/addresses/{address}/unblock")

    async def get_ipv6_statistics(self) -> dict:
        return await self._get("/api/v1/ipv6-pool/statistics")

    async def unblock_expired_ips(self) -> dict:
        return await self._post("/api/v1/ipv6-pool/maintenance/unblock-expired")

    # ── Monitoring (Admin) ────────────────────────────────────────────

    async def get_dashboard(self) -> dict:
        return await self._get("/api/v1/monitoring/dashboard")

    async def get_cache_tracking(self) -> dict:
        return await self._get("/api/v1/monitoring/cache-tracking")

    # ── Metrics ───────────────────────────────────────────────────────

    async def get_search_metrics(self) -> dict:
        return await self._get("/api/v1/metrics/search")
