"""Built-in example plugins package.

This package contains reference implementations of the PluginInterface protocol.
Each plugin directory contains a plugin.py module with a Plugin class that implements
the required interface for vision analysis tasks.

Available plugins:
- block_mapper: Map image colors to Minecraft block palette
- moderation: Content safety detection with sensitivity levels
- motion_detector: Detect motion between consecutive video frames
- ocr_plugin: Extract text from images using Tesseract OCR
"""
