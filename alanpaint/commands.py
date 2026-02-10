"""
Commands module for AlanPaint
Implements undo/redo functionality using command pattern
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from PIL import Image


class Command(ABC):
    """Abstract base class for commands"""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command"""
        pass
    
    @abstractmethod
    def redo(self) -> None:
        """Redo the command"""
        pass
    
    @abstractmethod
    def is_filter(self) -> bool:
        """Return True if this is a filter command"""
        pass


class DrawCommand(Command):
    """
    Command for drawing operations (brush, eraser, shapes)
    Stores the modified region as a separate image for memory efficiency
    """
    
    def __init__(self, master_image: Image.Image, modified_region: Image.Image, 
                 region: Tuple[int, int, int, int]):
        """
        Args:
            master_image: Reference to the master image
            modified_region: The modified portion as a separate image
            region: (x, y, width, height) of the modified region
        """
        self._master = master_image
        self._modified_region = modified_region
        self._region = region
        self._saved_region: Optional[Image.Image] = None
    
    def execute(self) -> None:
        """Apply the modification to master image"""
        x, y, w, h = self._region
        
        # Save the original region for undo
        self._saved_region = self._master.crop((x, y, x + w, y + h))
        
        # Paste the modified region
        self._master.paste(self._modified_region, (x, y))
    
    def undo(self) -> None:
        """Restore the original region"""
        if self._saved_region:
            x, y, w, h = self._region
            self._master.paste(self._saved_region, (x, y))
    
    def redo(self) -> None:
        """Reapply the modification"""
        self.execute()
    
    def is_filter(self) -> bool:
        return False
    
    @property
    def region(self) -> Tuple[int, int, int, int]:
        return self._region


class FilterCommand(Command):
    """
    Command for filter operations
    Stores the original full image for undo (limited by max_undo)
    """
    
    def __init__(self, master_image: Image.Image, filtered_image: Image.Image):
        self._master = master_image
        self._filtered = filtered_image
        self._original: Optional[Image.Image] = None
    
    def execute(self) -> None:
        """Apply the filter to master image"""
        # Save original for undo
        self._original = self._master.copy()
        
        # Replace master content
        self._master.paste(self._filtered)
    
    def undo(self) -> None:
        """Restore the original image"""
        if self._original:
            self._master.paste(self._original)
    
    def redo(self) -> None:
        """Reapply the filter"""
        self.execute()
    
    def is_filter(self) -> bool:
        return True


class TextCommand(Command):
    """Command for text insertion"""
    
    def __init__(self, master_image: Image.Image, text_region: Image.Image, 
                 region: Tuple[int, int, int, int]):
        self._master = master_image
        self._text_region = text_region
        self._region = region
        self._saved_region: Optional[Image.Image] = None
    
    def execute(self) -> None:
        x, y, w, h = self._region
        self._saved_region = self._master.crop((x, y, x + w, y + h))
        self._master.paste(self._text_region, (x, y))
    
    def undo(self) -> None:
        if self._saved_region:
            x, y, w, h = self._region
            self._master.paste(self._saved_region, (x, y))
    
    def redo(self) -> None:
        self.execute()
    
    def is_filter(self) -> bool:
        return False


class CommandManager:
    """
    Manages undo/redo history with configurable limits
    """
    
    def __init__(self, max_undo: int = 20):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._max_undo = max_undo
    
    def execute(self, command: Command) -> None:
        """Execute a command and add to undo stack"""
        command.execute()
        self._undo_stack.append(command)
        
        # Clear redo stack on new command
        self._redo_stack.clear()
        
        # Limit undo history
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
    
    def undo(self) -> bool:
        """Undo the last command"""
        if not self._undo_stack:
            return False
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return True
    
    def redo(self) -> bool:
        """Redo the last undone command"""
        if not self._redo_stack:
            return False
        
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)
        return True
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all history"""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def set_max_undo(self, max_undo: int) -> None:
        """Set maximum number of undo operations"""
        self._max_undo = max_undo
        
        # Trim if necessary
        while len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
    
    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)
    
    @property
    def redo_count(self) -> int:
        return len(self._redo_stack)
