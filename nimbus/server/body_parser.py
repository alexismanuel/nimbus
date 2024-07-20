import json
from typing import Any, Dict, Optional
from urllib.parse import parse_qs


class BodyParser:
    @classmethod
    async def parse(
        cls, headers: Dict[str, str], body: bytes
    ) -> Optional[Dict[str, Any]]:
        content_type = headers.get("content-type", "")

        if "application/json" in content_type:
            return await cls._parse_json(body)
        elif "application/x-www-form-urlencoded" in content_type:
            return await cls._parse_form_data(body)
        else:
            return None

    @classmethod
    async def _parse_json(cls, body: bytes) -> Dict[str, Any]:
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in request body")

    @classmethod
    async def _parse_form_data(cls, body: bytes) -> Dict[str, Any]:
        decoded = body.decode("utf-8")
        parsed = parse_qs(decoded)
        return {
            key: value[0] if len(value) == 1 else value for key, value in parsed.items()
        }
