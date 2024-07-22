import math
import random
from typing import List, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

Point = Tuple[float, float]

# Function To Generate Random Points
def generate_points(n_points : int, case : str) -> List[Point]:
    points : list[Point] = []
    if case == "rejection_sampling":
        while len(points) < n_points:
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)
            if x**2 + y**2 <= 1:
                points.append((x, y))
    elif case == "polar_coordinates":
        while len(points) < n_points:
            r = random.uniform(0, 1)
            theta = random.uniform(0, 2 * math.pi)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append((x, y))
    elif case == "inverse_tansform_sampling":
        while len(points) < n_points:
            r = math.sqrt(random.uniform(0, 1))
            theta = random.uniform(0, 2 * math.pi)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append((x, y))
    elif case == "infinite_triangle":
        while len(points) < n_points:
            a = random.uniform(0, 1)
            b = random.uniform(0, 1)
            theta = random.uniform(0, 2 * math.pi)

            r = a + b
            if r > 1:
                r = 2 - r

            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append((x, y))

    return points

def beautify_plot(fig : plt.Figure, ax : plt.Axes) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)

    fig.patch.set_facecolor("#2e2e2e")
    ax.set_facecolor("#2e2e2e")
    ax.axhline(y = 0, color = "white", linewidth = 0.5, linestyle = "--")
    ax.axvline(x = 0, color = "white", linewidth = 0.5, linestyle = "--")
    # ax.grid(True, color = "white", linestyle = "--", linewidth = 0.5)
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("white")

    circle = plt.Circle((0, 0), 1, edgecolor="#03a9f4", facecolor="none", linewidth = 1.5)
    ax.add_patch(circle)
    square = plt.Rectangle((-1, -1), 2, 2, edgecolor="#f44336", facecolor="none", linewidth = 1.5)
    ax.add_patch(square)

def create_animation(case : str, duration : int, fps : int, num_points : int = 1000, type : str = "gif") -> None:
    # Plot Setup
    fig, ax = plt.subplots()
    beautify_plot(fig, ax)

    (points,) = ax.plot([], [], "o", markersize = 0.8, color = "#8bc34a")
    text = ax.text(1.0, 1.05, '', color = "white", transform = ax.transAxes, ha = "right")

    points_list : List[Point] = []

    # Animation Initialization
    def init() -> Tuple[plt.Line2D]:
        points_list.clear()
        points.set_data([], [])
        text.set_text('')
        return points, text

    # Animation Updation
    def update(frame : int) -> Tuple[plt.Line2D]:
        pts_to_generate = num_points // (duration * fps)
        new_points = generate_points(pts_to_generate, case)
        points_list.extend(new_points)
        points.set_data(
            [point[0] for point in points_list], [point[1] for point in points_list]
        )
        text.set_text(f'Points: {len(points_list)}')
        return points, text

    # Animation Generation
    total_frames : int = duration * fps
    ani = FuncAnimation(fig, update, frames=range(total_frames), init_func=init, blit=True)

    # Animation Saving
    writer = PillowWriter(fps=fps)
    ani.save(f'{case}.{type}', writer=writer)

    plt.close(fig)


if __name__ == "__main__":
    duration = 10
    fps = 15
    num_points = 3000

    animation_types = ["rejection_sampling", "polar_coordinates", "inverse_tansform_sampling", "infinite_triangle"]

    for case in animation_types:
        create_animation(case, duration, fps, num_points, "gif")
        print(f"Animation for {case} created successfully & Saved as {case}.gif !")

    create_animation("init", duration, fps, 0, "png")
