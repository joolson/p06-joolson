# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from os.path import abspath, dirname, join

from PIL import Image
from tornado.testing import gen_test

from tests.base import TestCase
from thumbor.config import Config
from thumbor.context import Context, ServerParameters
from thumbor.importer import Importer


class ExtremeAspectResizeTestCase(TestCase):
    def get_context(self):
        cfg = Config(SECURITY_KEY="ACME-SEC")
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = abspath(
            join(dirname(__file__), "../course/images/")
        )
        cfg.STORAGE = "thumbor.storages.no_storage"

        importer = Importer(cfg)
        importer.import_modules()
        server = ServerParameters(
            8889, "localhost", "thumbor.conf", None, "info", None
        )
        server.security_key = "ACME-SEC"
        return Context(server, cfg, importer)

    async def get_image(self, path):
        response = await self.async_fetch(path)
        assert response.code == 200, (
            f"{path} returned {response.code}, not an image"
        )
        return Image.open(BytesIO(response.body))

    @gen_test
    async def test_extreme_aspect_ratio_returns_visible_picture(self):
        # 16x16 source asked for at 800x20: crop_height rounds to 0,
        # the image is cropped to nothing and comes back fully transparent.
        image = await self.get_image("/unsafe/800x20/rainbow.png")
        assert image.size == (800, 20)
        assert image.convert("RGBA").getchannel("A").getextrema()[1] > 0

        # A very wide source fit into 1x1: the 500 error instead of a 1x1.
        image = await self.get_image("/unsafe/fit-in/1x1/940x2.png")
        assert image.size == (1, 1)

        # Width only, height 0: the 500 error instead of a 100x1.
        image = await self.get_image("/unsafe/fit-in/100x0/940x2.png")
        assert image.size == (100, 1)