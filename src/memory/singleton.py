from src.memory.memory_manager import MemoryManager

# Global singleton instance
memory_manager = MemoryManager()

def get_memory_manager() -> MemoryManager:
    return memory_manager
