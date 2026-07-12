from typing import Dict, Callable, Any, Optional, List


class tool:  # @tool 把某个方法标记成一个可注册工具。它不是立即执行工具，而是在 ToolGroup 初始化时被扫描出来。
    """
    A tool that can be used to execute a function.
    """

    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self  # Return the descriptor itself when accessed from the class
        return lambda *args, **kwargs: self.func(instance, *args, **kwargs)


class ToolGroup:
    """
    A group of tools that can be used together.
    """

    def __init__(self, name: str):
        self.name = name
        self._tool_registry: Dict[str, Callable] = {}
        self._register_tools()

    def get_name(self):
        return self.name

    def _register_tools(self):
        '''原来的方法：
        def python_code(self, code):
        ...
        加上装饰器：
        @tool
        def python_code(self, code):
        ...
        在 Python 里等价于：
        python_code = tool(python_code)'''
        # Register all methods decorated with @tool
        # 只要某个方法上有 @tool，它就会进入 _tool_registry
        # Tool names must be unique across tool groups.
        # TODO: Support duplicate tool names across tool groups via namespacing
        for attr_name in dir(self): # dir(self) 会列出当前对象能访问到的所有属性名和方法名。
            # Look for the descriptor on the class, not the instance
            raw = getattr(type(self), attr_name, None)
            if isinstance(raw, tool): # 判断这个类属性是不是一个 tool 对象。
                self._tool_registry[raw.name] = getattr(self, attr_name)

    def get_tool(self, name: str) -> Optional[Callable]:
        # Get a tool by name, returns None if not found
        return self._tool_registry.get(name)

    def get_tool_names(self) -> List[str]:
        # Get all available tool names
        return list(self._tool_registry.keys())

    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        # Execute a tool by name with given arguments
        tool_func = self.get_tool(name)  # tool_func = EmbodiedRobosuiteToolGroup.python_code
        if tool_func:
            # If only one argument is passed and it's a dict, pass it as a single argument
            if len(args) == 1 and isinstance(args[0], dict):  # equal self.python_code(code=tool_input)
                return tool_func(**args[0]) #直接执行 go to /Users/zhouzhida/Desktop/test/TaskB/AlphaApollo/alphaapollo/core/tools/embodied_robosuite.py
            else:
                return tool_func(*args, **kwargs)
        raise ValueError(f"Tool '{name}' not found in group '{self.name}'.")

    def get_tool_to_group_mapping(self) -> Dict[str, str]:
        # Get mapping of tool names to group name
        return {name: self.name for name in self._tool_registry}
