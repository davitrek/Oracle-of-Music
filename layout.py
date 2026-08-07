from itertools import pairwise


def circle_centres(num: int, svg_width: int) -> list[float]:
    centres = []
    for i in range(num):
        centres.append(svg_width / (2 * num) * (2 * i + 1))

    return centres


def square_centres(circle_centres: list[float]):
    centres = []
    for previous, current in pairwise(circle_centres):
        centres.append((current + previous) / 2)

    return centres


def square_left_edges(
    square_centres: list[float], square_size: float
) -> list[float]:
    left_edges = []
    for square in square_centres:
        left_edges.append(square - square_size / 2)

    return left_edges


def line_positions(
    circle_rad: float,
    square_size: float,
    circle_centres: list[float],
    square_centres: list[float],
) -> list[tuple[float, float]]:
    positions = []
    for circle_first_pos, square_pos, circle_second_pos in zip(
        circle_centres, square_centres, circle_centres[1:]
    ):
        positions.append(
            (circle_first_pos + circle_rad, square_pos - square_size / 2)
        )
        positions.append(
            (square_pos + square_size / 2, circle_second_pos - circle_rad)
        )

    return positions
