from trader.strategy.grid.grid_utils import create_arithmetic_sequence, create_geometric_sequence, \
    create_fibonacci_sequence
from trader.strategy.grid.grid_utils import grid_percents, grid_prices


def print_grid_and_pct(g, msg):
    print(f"| {msg} |".center(80, '*'))
    print(f"格子数列：{g}")
    print(f"格子数列中每格占比：{grid_percents(g)}")
    print(f"区间 10000-20000 之间的网格：{grid_prices(10000, 20000, grid_percents(g))}")
    print()


print(create_arithmetic_sequence(10))
print(create_geometric_sequence(16))
print(create_geometric_sequence(4, 1.2))
print(create_geometric_sequence(10, 1.5))
print(create_fibonacci_sequence(10))

grid1 = [1 for i in range(1, 11, 1)]
print_grid_and_pct(grid1, "等差数列")

grid2 = [2 ** i for i in range(0, 10)]
print_grid_and_pct(grid2, "等比数列, 公比为：2")

grid3 = [1.5 ** i for i in range(0, 10)]
print_grid_and_pct(grid3, "等比数列, 公比为：1.5")

grid3 = [0.5 ** i for i in range(0, 10)]
print_grid_and_pct(grid3, "等比数列, 公比为：0.5")

fib = lambda n: n if n <= 2 else fib(n - 1) + fib(n - 2)
grid4 = [fib(i) for i in range(2, 12)]
print_grid_and_pct(grid4, "斐波那契额数列：2,3,5,8,...")

primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
print_grid_and_pct(primes, "质数数列")

custom = [1, 2, 3, 4, 5, 5, 4, 3, 2, 1]
print_grid_and_pct(custom, "自定义数列")

grid5 = [1 for _ in range(0, 20)]
print_grid_and_pct(grid5, "等差数列 20个格子")
