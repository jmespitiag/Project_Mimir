from __future__ import annotations
import logging
log = logging.getLogger('mimir.hermod')
class NotifyService:
    def send(self, channel: str, text: str) -> dict:
        log.info('notify channel=%s text=%s', channel, text[:120])
        return {'channel': channel, 'sent': True, 'preview': text[:120]}
