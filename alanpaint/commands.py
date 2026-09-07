"""Undoable edits with bounded history and a saved-document revision."""


def image_bytes(image):
    return image.width * image.height * len(image.getbands())


class DrawCommand:
    def __init__(self, master_image, modified_region, region):
        self.master = master_image
        self.region = region
        x, y, w, h = region
        self.before = master_image.crop((x, y, x+w, y+h))
        self.after = modified_region
        self.memory_bytes = image_bytes(self.before) + image_bytes(self.after)

    def execute(self):
        self.master.paste(self.after, self.region[:2])

    def undo(self):
        self.master.paste(self.before, self.region[:2])

    redo = execute


class FilterCommand(DrawCommand):
    def __init__(self, master_image, filtered_image):
        super().__init__(master_image, filtered_image, (0, 0, *master_image.size))


class ReplaceImageCommand:
    """Keep image identity so earlier region commands survive crop/resize."""
    def __init__(self, canvas, replacement):
        self.canvas = canvas
        self.before = canvas.get_image()
        self.after = replacement
        self.memory_bytes = image_bytes(self.before) + image_bytes(self.after)

    def execute(self):
        self.canvas.set_image(self.after)

    def undo(self):
        self.canvas.set_image(self.before)

    redo = execute


TextCommand = DrawCommand


class CommandManager:
    def __init__(self, max_undo=20, max_bytes=128 * 1024 * 1024):
        self._max_undo, self._max_bytes = max_undo, max_bytes
        self.clear()

    def clear(self):
        self._undo_stack, self._redo_stack = [], []
        self._revision = self._saved_revision = self._sequence = 0

    def execute(self, command):
        command.execute()
        command.previous_revision = self._revision
        self._sequence += 1
        command.revision = self._sequence
        self._revision = command.revision
        self._undo_stack.append(command)
        self._redo_stack.clear()
        # Retain the most recent operation even when it exceeds the budget.
        while len(self._undo_stack) > 1 and (len(self._undo_stack) > self._max_undo or
                sum(c.memory_bytes for c in self._undo_stack) > self._max_bytes):
            self._undo_stack.pop(0)

    def undo(self):
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo()
        self._revision = command.previous_revision
        self._redo_stack.append(command)
        return True

    def redo(self):
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.redo()
        self._revision = command.revision
        self._undo_stack.append(command)
        return True

    def mark_saved(self):
        self._saved_revision = self._revision

    @property
    def modified(self):
        return self._saved_revision != self._revision

    def can_undo(self):
        return bool(self._undo_stack)

    def can_redo(self):
        return bool(self._redo_stack)

    @property
    def undo_count(self):
        return len(self._undo_stack)

    @property
    def redo_count(self):
        return len(self._redo_stack)
