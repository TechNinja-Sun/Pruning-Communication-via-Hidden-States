from datetime import datetime
import os
from system.registry import PRUNE_COMM_REGISTRY


@PRUNE_COMM_REGISTRY.register('sys_memory')
class SysMemory:
    def __init__(self):
        self.memory_root_dir = "agent_output_memory"
        os.makedirs(self.memory_root_dir, exist_ok=True)
        self.agent_file_map = {}  

    def build_momory_space(self, agent_name: list):
        for name in agent_name:
            file_path = os.path.join(self.memory_root_dir, f"{name}.txt")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"=== {name} 输出存储文件 ===\n")
                f.write("="*30 + "\n\n")
            
            self.agent_file_map[name] = file_path
            print(f"创建 {name} 存储文件: {file_path}")
        return self.agent_file_map

    def add_memory(self, agent_name: str, output_content: str):
        file_path = self.agent_file_map.get(agent_name)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {agent_name}:\n")
            f.write(output_content + "\n\n")

    def clear_memory(self, agent_name: str):
        file_path = self.agent_file_map.get(agent_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"=== {agent_name} 输出存储文件 ===\n")
            f.write("="*30 + "\n\n")
        
        print(f"已擦除 {agent_name} 的所有记忆内容")

    def read_memory(self, agent_name: str) -> str:
        file_path = self.agent_file_map.get(agent_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"已读取 {agent_name} 的全部记忆")
        return content