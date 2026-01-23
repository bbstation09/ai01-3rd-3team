"""
Modules package initialization.
"""

from .popup_watcher import create_popup_watcher, PopupWatcher
from .vlm_handler import call_vlm, encode_image_to_base64

__all__ = [
    'create_popup_watcher',
    'PopupWatcher',
    'call_vlm',
    'encode_image_to_base64'
]
