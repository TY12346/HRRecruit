"""Firebase Cloud Messaging helpers for HRRecruit push notifications."""

from __future__ import annotations

import importlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from django.conf import settings

from .models import Notification, PushDevice


class FirebasePushUnavailable(Exception):
    """Raised when Firebase Admin SDK push delivery cannot be used."""


def firebase_push_configured() -> bool:
    """Return whether Firebase push delivery is intentionally enabled."""
    return bool(getattr(settings, 'FIREBASE_PUSH_ENABLED', False))


def firebase_push_status() -> dict:
    """Return setup status for diagnostics/admin checks."""
    dependencies_installed = _firebase_admin_available()
    credentials_configured = bool(
        getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
        or getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '')
        or getattr(settings, 'FIREBASE_USE_APPLICATION_DEFAULT_CREDENTIALS', False)
    )
    ready = firebase_push_configured() and dependencies_installed and credentials_configured
    return {
        'enabled': firebase_push_configured(),
        'dependencies_installed': dependencies_installed,
        'credentials_configured': credentials_configured,
        'ready': ready,
    }


def send_notification_push(notification: Notification) -> dict:
    """Send one stored notification to all active FCM tokens for the recipient."""
    devices = list(notification.recipient.push_devices.filter(is_active=True))
    if not devices:
        return {'provider': 'firebase_fcm', 'status': 'no_active_devices', 'success_count': 0, 'failure_count': 0}
    return send_push_to_devices(devices, notification.title, notification.message, data=_notification_data(notification))


def send_push_to_devices(devices: Iterable[PushDevice], title: str, body: str, data: dict | None = None) -> dict:
    """Send a Firebase multicast push to the supplied devices."""
    device_list = [device for device in devices if device.is_active and device.registration_token]
    if not device_list:
        return {'provider': 'firebase_fcm', 'status': 'no_active_devices', 'success_count': 0, 'failure_count': 0}
    if not firebase_push_configured():
        return {'provider': 'firebase_fcm', 'status': 'disabled', 'success_count': 0, 'failure_count': 0}

    messaging = _firebase_messaging_module()
    _firebase_app()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=[device.registration_token for device in device_list],
        data={str(key): str(value) for key, value in (data or {}).items() if value is not None},
    )
    try:
        response = messaging.send_each_for_multicast(message)
    except AttributeError:
        response = messaging.send_multicast(message)
    _deactivate_failed_tokens(device_list, getattr(response, 'responses', []))
    return {
        'provider': 'firebase_fcm',
        'status': 'sent',
        'success_count': int(getattr(response, 'success_count', 0)),
        'failure_count': int(getattr(response, 'failure_count', 0)),
    }


def _notification_data(notification: Notification) -> dict:
    return {
        'notification_id': notification.id,
        'notification_type': notification.notification_type,
        'related_entity_type': notification.related_entity_type,
        'related_entity_id': notification.related_entity_id,
    }


def _deactivate_failed_tokens(devices: list[PushDevice], responses: list) -> None:
    failed_ids = [device.id for device, response in zip(devices, responses, strict=False) if not getattr(response, 'success', False)]
    if failed_ids:
        PushDevice.objects.filter(id__in=failed_ids).update(is_active=False)


def _firebase_admin_available() -> bool:
    return importlib.util.find_spec('firebase_admin') is not None


def _firebase_messaging_module():
    if not _firebase_admin_available():
        raise FirebasePushUnavailable('firebase-admin is not installed.')
    return importlib.import_module('firebase_admin.messaging')


@lru_cache(maxsize=1)
def _firebase_app():
    if not firebase_push_configured():
        raise FirebasePushUnavailable('Firebase push is disabled. Set FIREBASE_PUSH_ENABLED=True.')
    if not _firebase_admin_available():
        raise FirebasePushUnavailable('firebase-admin is not installed.')

    firebase_admin = importlib.import_module('firebase_admin')
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    credential = _firebase_credential()
    project_id = getattr(settings, 'FIREBASE_PROJECT_ID', '')
    options = {'projectId': project_id} if project_id else None
    return firebase_admin.initialize_app(credential, options=options)


def _firebase_credential():
    credentials_module = importlib.import_module('firebase_admin.credentials')
    credentials_json = getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '')
    credentials_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
    if credentials_json:
        try:
            return credentials_module.Certificate(json.loads(credentials_json))
        except json.JSONDecodeError as exc:
            raise FirebasePushUnavailable('FIREBASE_CREDENTIALS_JSON is not valid JSON.') from exc
    if credentials_path:
        path = Path(credentials_path)
        if not path.exists():
            raise FirebasePushUnavailable(f'Firebase credentials file does not exist: {path}')
        return credentials_module.Certificate(str(path))
    if getattr(settings, 'FIREBASE_USE_APPLICATION_DEFAULT_CREDENTIALS', False):
        return credentials_module.ApplicationDefault()
    raise FirebasePushUnavailable('Configure FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON for Firebase push notifications.')
