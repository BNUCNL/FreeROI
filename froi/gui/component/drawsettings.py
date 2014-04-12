# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Drawing settings class"""


class PainterStatus(object):
    """
    Use the Stragety pattern.

    """
    def __init__(self, draw_settings):
        self.draw_settings = draw_settings

    def set_draw_settings(self, draw_settings):
        self.draw_settings = draw_settings

    def get_draw_settings(self):
        return self.draw_settings

    def is_view(self):
        return self.draw_settings.is_view()

    def is_brush(self):
        return self.draw_settings.is_brush()

    def is_eraser(self):
        return self.draw_settings.is_eraser()

    def is_hand(self):
        return self.draw_settings.is_hand()

    def is_roi_tool(self):
        return self.draw_settings.is_roi_tool()

    def is_roi_selection(self):
        return self.draw_settings.is_roi_selection()

    def is_drawing_valid(self):
        return self.draw_settings.is_drawing_valid()

    def get_drawing_value(self):
        return self.draw_settings.get_drawing_value()

    def get_drawing_size(self):
        return self.draw_settings.get_drawing_size()

    def get_drawing_color(self):
        return self.draw_settings.get_drawing_color()

class DrawSettings(object):
    """
    Settings for cursor status.

    """
    def is_view(self):
        return False
    
    def is_brush(self):
        return False

    def is_eraser(self):
        return False

    def is_hand(self):
        return False

    def is_roi_tool(self):
        return False

    def is_roi_selection(self):
        return False

    def is_drawing_valid(self):
        return False

    def get_drawing_value(self):
        raise NotImplementedError

    def get_drawing_size(self):
        raise NotImplementedError

    def get_drawing_color(self):
        raise NotImplementedError

class ViewSettings(DrawSettings):
    def __init__(self):
        super(ViewSettings, self).__init__()

    def is_view(self):
        return True

class MoveSettings(DrawSettings):
    def __init__(self):
        super(MoveSettings, self).__init__()

    def is_hand(self):
        return True
