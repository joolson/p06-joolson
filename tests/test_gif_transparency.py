# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2025 globo.com thumbor@googlegroups.com

# Regression coverage for issue #3: resized GIF loses its transparent
# background.
#
# sticker.gif is a palette source with a transparent index. With the default
# PILLOW_PRESERVE_INDEXED_MODE, resizing quantizes the RGBA image back to P.
# The palette keeps its alpha, but info["transparency"] is not set, and the
# GIF writer receives an already indexed image, so the result comes back
# fully opaque. A resize must not change which pixels are transparent.

from io import BytesIO
from os.path import abspath, dirname, join
from unittest import TestCase

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

FIXTURES_PATH = abspath(join(dirname(__file__), "../course/images"))


class GifTransparencyTestCase(TestCase):
    def get_context(self):
        cfg = Config(
            SECURITY_KEY="ACME-SEC",
            ENGINE="thumbor.engines.pil",
            PILLOW_PRESERVE_INDEXED_MODE=True,
        )
        return Context(config=cfg)

    def test_resized_gif_keeps_its_transparent_background(self):
        source_path = join(FIXTURES_PATH, "sticker.gif")

        with open(source_path, "rb") as source_file:
            source_buffer = source_file.read()

        source = Image.open(BytesIO(source_buffer))

        # The source is a palette GIF with a transparent index.
        assert source.mode == "P"
        assert "transparency" in source.info

        source_alpha = source.convert("RGBA").getchannel("A")

        engine = Engine(self.get_context())
        engine.load(source_buffer, ".gif")
        engine.resize(240, 160)

        result = Image.open(BytesIO(engine.read(".gif")))

        # The resized GIF must still carry a transparency index.
        assert result.mode == "P"
        assert result.format == "GIF"
        assert "transparency" in result.info

        # The pixels transparent in the source are transparent in the output.
        result_alpha = result.convert("RGBA").getchannel("A")

        assert result_alpha.getextrema() == (0, 255)
        assert result_alpha.getextrema() == source_alpha.getextrema()