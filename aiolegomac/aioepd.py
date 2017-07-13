# Original Copyright 2013 Pervasive Displays, Inc.
# Modified Copyright 2017 Benjamin Bertrand
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.


import os
import re
import textwrap
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageOps

WHITE = 1
BLACK = 0


class EPDError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Clock:

    FONT_FILE = 'LiberationMono-Bold.ttf'
    CLOCK_FONT_SIZE = 100
    DATE_FONT_SIZE = 42
    WEEKDAY_FONT_SIZE = 42
    X_OFFSET = 5
    Y_OFFSET = 3
    COLON_SIZE = 5
    COLON_GAP = 10
    DATE_X = 10
    DATE_Y = 90
    WEEKDAY_X = 10
    WEEKDAY_Y = 130

    def __init__(self, epd):
        self.epd = epd
        # initially set all white background
        self.image = Image.new('1', self.epd.size, WHITE)
        # prepare for drawing
        self.draw = ImageDraw.Draw(self.image)
        self.width, self.height = self.image.size
        self.clock_font = ImageFont.truetype(Clock.FONT_FILE, Clock.CLOCK_FONT_SIZE)
        self.date_font = ImageFont.truetype(Clock.FONT_FILE, Clock.DATE_FONT_SIZE)
        self.weekday_font = ImageFont.truetype(Clock.FONT_FILE, Clock.WEEKDAY_FONT_SIZE)
        self.colon_x1 = self.width / 2 - Clock.COLON_SIZE
        self.colon_x2 = self.width / 2 + Clock.COLON_SIZE
        self.colon_y1 = Clock.CLOCK_FONT_SIZE / 2 + Clock.Y_OFFSET - Clock.COLON_SIZE
        self.colon_y2 = Clock.CLOCK_FONT_SIZE / 2 + Clock.Y_OFFSET + Clock.COLON_SIZE
        # clear the display buffer
        self.draw.rectangle((0, 0, self.width, self.height), fill=WHITE, outline=WHITE)
        self.previous_day = None

    async def display(self, now):
        if now.day != self.previous_day:
            self.draw.rectangle((1, 1, self.width - 1, self.height - 1), fill=WHITE, outline=BLACK)
            self.draw.rectangle((2, 2, self.width - 2, self.height - 2), fill=WHITE, outline=BLACK)
            self.draw.text((Clock.DATE_X, Clock.DATE_Y), now.strftime('%Y-%m-%d'), fill=BLACK, font=self.date_font)
            self.draw.text((Clock.WEEKDAY_X, Clock.WEEKDAY_Y), now.strftime('%A').upper(), fill=BLACK, font=self.weekday_font)
            self.previous_day = now.day
        else:
            self.draw.rectangle((Clock.X_OFFSET, Clock.Y_OFFSET, self.width - Clock.X_OFFSET, Clock.DATE_Y - 1), fill=WHITE, outline=WHITE)
        self.draw.text((Clock.X_OFFSET, Clock.Y_OFFSET), now.strftime('%H'), fill=BLACK, font=self.clock_font)
        self.draw.rectangle((self.colon_x1, self.colon_y1 - Clock.COLON_GAP, self.colon_x2, self.colon_y2 - Clock.COLON_GAP), fill=BLACK, outline=BLACK)
        self.draw.rectangle((self.colon_x1, self.colon_y1 + Clock.COLON_GAP, self.colon_x2, self.colon_y2 + Clock.COLON_GAP), fill=BLACK, outline=BLACK)
        self.draw.text((Clock.X_OFFSET + self.width / 2, Clock.Y_OFFSET), now.strftime('%M'), fill=BLACK, font=self.clock_font)
        # display image on the panel
        await self.epd.display(self.image)


class EPD(object):
    """EPD E-Ink interface

    To use:
    from aioepd import EPD

    epd = await EPD.create([path='/path/to/epd'], [auto=boolean])

    image = Image.new('1', epd.size, 0)
    # draw on image
    await epd.clear()         # clear the panel
    await epd.display(image)  # tranfer image data
    await epd.update()        # refresh the panel image - not needed if auto=true
    """

    PANEL_RE = re.compile('^([A-Za-z]+)\s+(\d+\.\d+)\s+(\d+)x(\d+)\s+COG\s+(\d+)\s*$', flags=0)

    def __init__(self, *args, **kwargs):
        self._epd_path = '/dev/epd'
        self._width = 200
        self._height = 96
        self._panel = 'EPD 2.0'
        self._cog = 0
        self._auto = False
        if len(args) > 0:
            self._epd_path = args[0]
        elif 'epd' in kwargs:
            self._epd_path = kwargs['epd']
        if ('auto' in kwargs) and kwargs['auto']:
            self._auto = True
        self._user_font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 20)
        self._msg_font = ImageFont.truetype('LiberationMono-Bold.ttf', 18)

    @classmethod
    async def create(cls, *args, **kwargs):
        self = EPD(*args, **kwargs)
        async with aiofiles.open(os.path.join(self._epd_path, 'version')) as f:
            version = await f.readline()
            self._version = version.rstrip('\n')
        async with aiofiles.open(os.path.join(self._epd_path, 'panel')) as f:
            line = await f.readline()
            m = self.PANEL_RE.match(line.rstrip('\n'))
            if m is None:
                raise EPDError('invalid panel string')
            self._panel = m.group(1) + ' ' + m.group(2)
            self._width = int(m.group(3))
            self._height = int(m.group(4))
            self._cog = int(m.group(5))
        if self._width < 1 or self._height < 1:
            raise EPDError('invalid panel geometry')
        self._msg_image = Image.new('1', self.size, WHITE)
        self._msg_draw = ImageDraw.Draw(self._msg_image)
        return self

    @property
    def size(self):
        return (self._width, self._height)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def panel(self):
        return self._panel

    @property
    def version(self):
        return self._version

    @property
    def cog(self):
        return self._cog

    @property
    def auto(self):
        return self._auto

    @auto.setter
    def auto(self, flag):
        if flag:
            self._auto = True
        else:
            self._auto = False

    async def display(self, image):
        # attempt grayscale conversion, ath then to single bit
        # better to do this before callin this if the image is to
        # be dispayed several times
        if image.mode != "1":
            image = ImageOps.grayscale(image).convert("1", dither=Image.FLOYDSTEINBERG)
        if image.mode != "1":
            raise EPDError('only single bit images are supported')
        if image.size != self.size:
            raise EPDError('image size mismatch')
        async with aiofiles.open(os.path.join(self._epd_path, 'LE', 'display_inverse'), 'r+b') as f:
            await f.write(image.tobytes())
        if self.auto:
            await self.update()

    async def display_message(self, message, username, now):
        # clear the display buffer
        self._msg_draw.rectangle((0, 0, self.width, self.height), fill=WHITE, outline=WHITE)
        # Get the number of characters per line to wrap the message
        (msg_width, msg_height) = self._msg_font.getsize(message)
        width_one_char = msg_width / len(message)
        # Keep a small margin on each side
        char_per_line = (self.width - 8) // width_one_char
        multi_line = textwrap.fill(message, char_per_line)
        self._msg_draw.text((4, 4), multi_line, fill=BLACK, font=self._msg_font)
        # Right-align the username and time of the message on the last line
        line = f'{username} at {now.strftime("%H:%M")}'
        (line_width, line_height) = self._user_font.getsize(line)
        x = self.width - line_width - 5
        y = self.height - line_height - 4
        self._msg_draw.text((x, y), line, fill=BLACK, font=self._user_font)
        await self.display(self._msg_image)

    async def update(self):
        await self._command(b'U')

    async def partial_update(self):
        await self._command(b'P')

    async def clear(self):
        await self._command(b'C')

    async def _command(self, c):
        async with aiofiles.open(os.path.join(self._epd_path, 'command'), 'wb') as f:
            await f.write(c)
