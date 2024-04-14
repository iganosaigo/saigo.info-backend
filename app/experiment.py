from enum import IntEnum


class T(IntEnum):
    admin = 1
    user = 1


print(T["admin"])
