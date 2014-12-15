# Copyright 2014 Letv Cloud Computing
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import random

from django.conf import settings
from django.http import HttpResponse  # noqa

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import StringIO

from math import ceil  # noqa

FONTS_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'fonts')

SESSION_KEY = getattr(settings,
                      "VERIFY_CODE_SESSION_KEY",
                      "letv_openstack_portal_verify_code")
IMAGE_WIDTH = getattr(settings,
                      "VERIFY_CODE_IMAGE_WIDTH", 180)
IMAGE_HEIGHT = getattr(settings,
                       "VERIFY_CODE_IMAGE_HEIGHT", 30)


class VerifyCode(object):
    """Class for gif image generation."""

    def __init__(self, request):
        self.django_request = request

    def _set_answer(self, answer):
        self.django_request.session[SESSION_KEY] = str(answer)

    @staticmethod
    def r(num1, num2):
        return random.randrange(num1, num2)

    def _yield_code(self):
        range_start, range_end = 1, 50
        num_1 = self.r(range_start, range_end)
        num_2 = self.r(range_start, range_end)

        if 0 == random.choice((0, 1)):
            code = "%s - %s = ?" % (num_1, num_2)
            result = num_1 - num_2
        else:
            code = "%s + %s = ?" % (num_1, num_2)
            result = num_1 + num_2
        self._set_answer(result)
        return code

    def _get_font_size(self):
        s1 = int(IMAGE_HEIGHT * 0.8)
        s2 = int(IMAGE_WIDTH / len(self.code))
        return int(min((s1, s2)) + max((s1, s2)) * 0.05)

    def get_verify_code(self):
        self.django_request.session[SESSION_KEY] = ''

        self.font_color = ['black', 'darkblue', 'darkred', 'red']
        self.background = (self.r(230, 255),
                           self.r(230, 255),
                           self.r(230, 255))

        # Image object
        img = Image.new('RGB',
                       (IMAGE_WIDTH, IMAGE_HEIGHT),
                        self.background)

        self.code = self._yield_code()
        self.font_size = self._get_font_size()
        # Paint brush
        draw = ImageDraw.Draw(img)

        # draw the interfering line
        for i in range(self.r(2, 4)):
            line_color = (self.r(0, 255),
                          self.r(0, 255),
                          self.r(0, 255))
            line_pos = (self.r(0, int(IMAGE_WIDTH * 0.2)),
                        self.r(0, IMAGE_HEIGHT),
                        self.r(3 * IMAGE_WIDTH / 4, IMAGE_WIDTH),
                        self.r(0, IMAGE_HEIGHT))
            draw.line(line_pos,
                      fill=line_color,
                      width=int(self.font_size * 0.1))

        # the start character position - X coordinates
        pos_x = self.r(int(self.font_size * 0.1), int(self.font_size * 0.9))

        # draw str, e.g.'10 - 2 = ?'
        for i in self.code:
            size_offset = int(len(self.code))
            pos_y = self.r(1, 3)

            if i in ('+', '=', '?'):
                size_offset = ceil(self.font_size * 0.9)
            else:
                size_offset = self.r(0,
                                     int(45 / self.font_size) +
                                     int(self.font_size / 5))
            # each character has a random font type
            font_path = os.path.join(
                FONTS_FOLDER_PATH,
                'font_type%i.ttf' % self.r(0, 6)
            ).replace('\\', '/')
            self.font = ImageFont.truetype(font_path,
                                           self.font_size +
                                           int(ceil(size_offset)))
            draw.text((pos_x, pos_y), i, font=self.font,
                      fill=random.choice(self.font_color))
            # net character X coordinates
            pos_x += self.font_size * 0.9

        buf = StringIO.StringIO()
        img.save(buf, 'gif')
        buf.closed
        # return image response
        return HttpResponse(buf.getvalue(), 'image/gif')

    @staticmethod
    def check(request, code):
        _code = request.session.get(SESSION_KEY, '')
        code = str(code).lower()
        return _code.lower() == code
