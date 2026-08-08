"""Windows Event Log collector using stdlib ctypes (wevtapi.dll).

Zero extra C-extension dependencies required (runs natively on standard Python / PyInstaller).
Reads Application, System, and Security event logs incrementally.
"""
from __future__ import annotations
import ctypes
import logging
import sys
from xml.etree import ElementTree as ET

from .base import Collector, utcnow_iso

log = logging.getLogger("corp_hub_agent")


class LogsWindowsCollector(Collector):
    name = "logs"

    def __init__(
        self,
        sources: list[str] | None = None,
        syslog_path: str | None = None,
        auth_log_path: str | None = None,
        max_lines_per_push: int = 500,
        max_backlog: int = 5000,
    ):
        self.sources = sources or ["Application", "System", "Security"]
        self.max_lines_per_push = max_lines_per_push
        self._bookmarks: dict[str, str] = {}

    def collect(self) -> dict:
        if sys.platform != "win32":
            return {"items": []}

        items = []
        for channel in self.sources:
            try:
                events = self._read_channel(channel)
                items.extend(events)
            except Exception as e:
                log.warning("Failed to read Windows Event Log channel %s: %s", channel, e)

            if len(items) >= self.max_lines_per_push:
                items = items[: self.max_lines_per_push]
                break

        return {"items": items}

    def _read_channel(self, channel: str) -> list[dict]:
        """Query EventLog channel using Windows API EvtQuery/EvtNext."""
        wevtapi = getattr(ctypes, "windll", None)
        if wevtapi is None or not hasattr(wevtapi, "wevtapi"):
            return []

        # EvtQuery(NULL, channel, "*", EvtQueryChannelPath | EvtQueryForwardDirection)
        EVT_QUERY_CHANNEL_PATH = 0x1
        EVT_QUERY_FORWARD_DIRECTION = 0x100
        
        flags = EVT_QUERY_CHANNEL_PATH | EVT_QUERY_FORWARD_DIRECTION
        query_handle = wevtapi.wevtapi.EvtQuery(
            None,
            ctypes.c_wchar_p(channel),
            ctypes.c_wchar_p("*"),
            flags,
        )
        if not query_handle:
            return []

        events = []
        try:
            array_size = 10
            events_handle = (ctypes.c_void_p * array_size)()
            returned = ctypes.c_ulong()

            while len(events) < self.max_lines_per_push:
                res = wevtapi.wevtapi.EvtNext(
                    query_handle,
                    array_size,
                    events_handle,
                    1000,  # 1s timeout
                    0,
                    ctypes.byref(returned),
                )
                if not res or returned.value == 0:
                    break

                for i in range(returned.value):
                    evt_h = events_handle[i]
                    parsed = self._render_event(wevtapi, evt_h, channel)
                    if parsed:
                        events.append(parsed)
                    wevtapi.wevtapi.EvtClose(evt_h)

        finally:
            wevtapi.wevtapi.EvtClose(query_handle)

        return events

    def _render_event(self, wevtapi, evt_h, channel: str) -> dict | None:
        """Render event handle into XML and parse basic fields."""
        EvtRenderEventXml = 1
        buffer_size = ctypes.c_ulong()
        buffer_used = ctypes.c_ulong()
        property_count = ctypes.c_ulong()

        wevtapi.wevtapi.EvtRender(
            None,
            evt_h,
            EvtRenderEventXml,
            0,
            None,
            ctypes.byref(buffer_used),
            ctypes.byref(property_count),
        )

        if buffer_used.value == 0:
            return None

        buf = ctypes.create_unicode_buffer(buffer_used.value)
        res = wevtapi.wevtapi.EvtRender(
            None,
            evt_h,
            EvtRenderEventXml,
            buffer_used.value,
            buf,
            ctypes.byref(buffer_used),
            ctypes.byref(property_count),
        )
        if not res:
            return None

        xml_str = buf.value
        try:
            root = ET.fromstring(xml_str)
            ns = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}
            
            system = root.find("ns:System", ns)
            time_created = system.find("ns:TimeCreated", ns) if system is not None else None
            ts = time_created.attrib.get("SystemTime") if time_created is not None else utcnow_iso()

            level_elem = system.find("ns:Level", ns) if system is not None else None
            level_code = level_elem.text if (level_elem is not None and level_elem.text) else "4"
            severity_map = {"1": "CRITICAL", "2": "ERROR", "3": "WARNING", "4": "INFO"}
            severity = severity_map.get(str(level_code), "INFO")

            provider = system.find("ns:Provider", ns) if system is not None else None
            facility = provider.attrib.get("Name") if provider is not None else channel

            event_id_elem = system.find("ns:EventID", ns) if system is not None else None
            event_id = event_id_elem.text if event_id_elem is not None else "0"

            message = f"EventID={event_id} Channel={channel} Facility={facility}"

            return {
                "ts": ts,
                "source": f"windows_{channel.lower()}",
                "facility": facility,
                "severity": severity,
                "message": message,
                "raw": {"xml": xml_str[:1000]},
            }
        except Exception:
            return {
                "ts": utcnow_iso(),
                "source": f"windows_{channel.lower()}",
                "facility": channel,
                "severity": "INFO",
                "message": f"Windows Event from {channel}",
                "raw": None,
            }
