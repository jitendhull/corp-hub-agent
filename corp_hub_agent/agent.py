"""Agent main loop: register (once), then push collectors on intervals."""
from __future__ import annotations
import argparse
import asyncio
import logging
import signal
import sys
import time

from .auth import read_token
from .collectors import LogsCollector, MetricsCollector, NetworkCollector, SysinfoCollector
from .config import Config, load_config
from .push import push
from .register import register

log = logging.getLogger("corp_hub_agent")

INTERVAL_KEY = {
    "metrics": "network_interval_seconds",
    "sysinfo": "sysinfo_interval_seconds",
    "network": "network_interval_seconds",
    "logs": "logs_interval_seconds",
}
POST_PATH = {
    "metrics": "/api/metrics/ingest",
    "sysinfo": "/api/agents/{host_id}/sysinfo",
    "network": "/api/agents/{host_id}/network",
    "logs": "/api/agents/{host_id}/logs",
}


class Runner:
    def __init__(self, config: Config, token: str, host_id: str):
        self.config = config
        self.token = token
        self.host_id = host_id
        self.running = True
        version = __import__("corp_hub_agent").__version__
        self.collectors = {
            "metrics": MetricsCollector(agent_version=version),
            "sysinfo": SysinfoCollector(agent_version=version),
            "network": NetworkCollector(),
            "logs": LogsCollector(
                sources=config.logs.sources,
                syslog_path=config.logs.syslog_path,
                auth_log_path=config.logs.auth_log_path,
                max_lines_per_push=config.logs.max_lines_per_push,
                max_backlog=config.logs.max_backlog,
            ),
        }

    async def run(self) -> None:
        tasks = [asyncio.create_task(self._loop(name)) for name in self.collectors]
        await asyncio.gather(*tasks)

    async def _loop(self, name: str) -> None:
        interval = getattr(self.config, INTERVAL_KEY[name])
        while self.running:
            try:
                payload = self.collectors[name].collect()
                path = POST_PATH[name].format(host_id=self.host_id)
                if name == "logs" and not payload["items"]:
                    pass  # nothing new — skip push
                else:
                    await asyncio.to_thread(push, self.config.backend_url, self.token, path, payload)
            except Exception as e:
                log.exception("collector %s failed: %s", name, e)
            await asyncio.sleep(interval)

    def stop(self) -> None:
        self.running = False


async def _async_main(config: Config) -> int:
    token = read_token(config.token_path)
    host_id = None

    if token is None:
        log.info("No token — registering with %s", config.backend_url)
        try:
            host_id, token = await asyncio.to_thread(register, config, config.token_path)
            log.info("Registered. host_id=%s", host_id)
        except Exception as e:
            log.error("Registration failed: %s", e)
            return 1
    else:
        # Host id not stored locally — derive from token by asking backend?
        # v1: re-register (idempotent, backend returns same token).
        try:
            host_id, token = await asyncio.to_thread(register, config, config.token_path)
        except Exception as e:
            log.error("Re-register failed: %s", e)
            return 1

    runner = Runner(config, token, host_id)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, runner.stop)
        except NotImplementedError:
            pass

    log.info("Starting collectors (host=%s)", host_id)
    await runner.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corp-Hub agent")
    parser.add_argument("--config", help="path to agent.conf")
    parser.add_argument("--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    try:
        return asyncio.run(_async_main(config))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
