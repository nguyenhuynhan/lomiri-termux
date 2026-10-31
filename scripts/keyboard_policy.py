"""Keep automatic keyboard requests separate from the user's manual toggle."""


class KeyboardPolicy:
    def __init__(self, size):
        self.full_heights = {size[0]: size[1], size[1]: size[0]}
        self.visible = False
        self.owned = False
        self.focused = False
        self.pending = None

    def viewport(self, size):
        width, height = size
        full = max(self.full_heights.get(width, height), height)
        self.full_heights[width] = full
        was_visible = self.visible
        self.visible = full - height > max(120, full * .15)
        if self.pending is not None and self.visible == self.pending:
            self.owned = self.pending
            self.pending = None
        elif was_visible and not self.visible:
            self.owned = False
        return self.visible

    def request(self, focused, automatic=True, force=False):
        desired = focused and automatic
        if desired == self.focused and not force:
            return None
        self.focused = desired
        if self.pending is not None:
            return None
        return self.reconcile()

    def reconcile(self):
        if self.pending is not None:
            return None
        if self.focused and not self.visible:
            self.pending = True
            return True
        if not self.focused and self.visible and self.owned:
            self.pending = False
            return False
        return None

    def failed(self):
        self.pending = None
