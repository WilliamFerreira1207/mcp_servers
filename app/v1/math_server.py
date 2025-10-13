# main.py
from mcp.server.fastmcp import FastMCP
import math, sys
import os
mcp = FastMCP(name="math-tools-mcp", host="0.0.0.0", stateless_http=True)

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

def compute_factorial(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    return math.factorial(n)

@mcp.tool()  # ← sin kwargs; el schema sale de las anotaciones
def factorial_value(n: int) -> int:
    """Return the exact value of n! (factorial of n). Example: factorial_value(5) -> 120"""
    return compute_factorial(n)  # → output_schema = {"result": {"type": "integer"}}

@mcp.tool()
def factorial_digits(n: int) -> int:
    """Return the number of digits in n! (factorial of n). Example: factorial_digits(5) -> 3"""
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n <= 1:
        return 1
    s = 0.0
    for i in range(2, n + 1):
        s += math.log10(i)
    return int(math.floor(s)) + 1

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
