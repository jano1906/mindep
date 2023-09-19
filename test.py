from typing import Any
from dataclasses import dataclass

class Var:
    value = 1
    def __init__(self, t=int):
        self.t = t
        print(f"created var with {type(t)}")
    
    def __get__(self, instance, owner):
        print("get", instance, owner)
        return self.value
    def __set__(self, instance, value):
        print("set", instance)
        self.value = float(value)

def decorator(cls):
    print(cls.__dict__)
    return cls




@decorator
class A:
    x: range(4,10)
    y: str = 1
    def __getattribute__(self, __name: str) -> Any:
        print(__name)
        return object.__getattribute__(self, __name)

    def f(self):
        self.x = 2
        print(self.x)
        print(self.y)

A().f()