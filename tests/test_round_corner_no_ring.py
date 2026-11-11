# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2025 globo.com thumbor@googlegroups.com

# Regression coverage for issue #2: transparent rounded corners carry a dark
# ring.
#
# round_corner(...,1) must smooth the arc through the alpha channel: the edge
# pixels keep their original color and become partly transparent. Today the
# edge pixels keep alpha 255 and their RGB is scaled toward black, which is
# the dark ring over any background.

from tornado.testing import gen_test

from tests.base import FilterTestCase


class RoundCornerNoRingTestCase(FilterTestCase):
    @gen_test
    async def test_transparent_round_corner_edge_fades_through_alpha(self):
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            "round_corner(50,255,255,255,1)",
            mode="RGBA",
        )

        source = self.get_fixture("source.jpg", mode="RGBA")

        assert image.mode == "RGBA"

        # Walk the anti-aliased arc in the top-left corner. A pixel is on the
        # edge when the filter changed it. With the fix each such pixel keeps
        # its source color and is made partly transparent.
        darkened = []
        for y in range(0, 51):
            for x in range(0, 51):
                if image.getpixel((x, y)) == source.getpixel((x, y)):
                    continue

                red, green, blue, alpha = image.getpixel((x, y))
                src_red, src_green, src_blue, _ = source.getpixel((x, y))

                # The band is either fully transparent or the opaque fill.
                if alpha in (0, 255):
                    # An opaque edge pixel must not have been darkened.
                    if alpha == 255 and (red, green, blue) != (
                        src_red,
                        src_green,
                        src_blue,
                    ):
                        darkened.append(((x, y), (red, green, blue), alpha))

        assert not darkened, (
            "round_corner with transparency darkened these edge pixels "
            f"instead of fading them through alpha: {darkened[:5]}"
        )