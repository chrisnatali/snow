import os, random, time
import argparse
import re
import threading


class Snow:
    def __init__(self, height: int, width: int, intensity: int):
        self.height = height
        self.width = width
        self.intensity = intensity
        # Flakes are tuples of (row, column)
        self.flakes = []

    def new_flakes(self) -> list[tuple[int, int]]:
        """adds flakes to 0 to 9% of top rows columns based on intensity"""
        num_flakes = int(self.width * self.intensity / 100)
        return [(0, col) for col in random.sample(range(self.width), k=num_flakes)]

    @staticmethod
    def moved_flakes(flakes: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """move flakes down and randomly shimmy them"""
        return [(row + 1, col + random.choice([-1, 0, 1])) for (row, col) in flakes]

    def update_flakes(self):
        """Each tick, flakes should be updated
        1. Move existing flakes
        2. Remove flakes that fall out of bottom (but leave any that might fall outside of width since
        they may come back into view later)
        3. Introduce new flakes
        """
        self.flakes = self.moved_flakes(self.flakes)
        self.flakes += self.new_flakes()
        self.flakes = [(row, col) for (row, col) in self.flakes if row < self.height]

    def render(self) -> str:
        grid = [[" "] * self.width for _ in range(self.height)]
        for row, col in self.flakes:
            if row < self.height and col < self.width:
                grid[row][col] = "*"

        return "\n".join(("".join(row) for row in grid))


class CheckRange(argparse.Action):
    def __init__(self, *args, **kwargs):
        if "range" not in kwargs:
            raise ValueError("a range must be specified")

        if not issubclass(type(kwargs["range"]), range):
            raise ValueError("range must be of type range")

        self.range = kwargs.pop("range")
        super().__init__(*args, **kwargs)

    def __call__(self, _parser, namespace, values, _option_string=None):
        if values not in self.range:
            raise argparse.ArgumentError(self, f"{values} not in {range}")
        setattr(namespace, self.dest, values)


def main():
    parser = argparse.ArgumentParser(description="Generate Snowflake Scene in Terminal")

    parser.add_argument(
        "--tick_rate-ms",
        "-t",
        type=int,
        default=100,
        action=CheckRange,
        range=range(1, 1000),
        help="The tick rate in ms (default: 100).",
    )

    parser.add_argument(
        "--width", "-w", type=int, default=100, help="The width of the scene"
    )

    parser.add_argument(
        "--height", "-e", type=int, default=30, help="The height of the scene"
    )

    parser.add_argument(
        "--intensity",
        "-i",
        type=int,
        default=2,
        action=CheckRange,
        range=range(0, 10),
        help="The intensity of snowfall from 0 to 9",
    )

    args = parser.parse_args()

    # The snow object will be shared between threads to allow interactivity while generating
    # the simulation
    snow = Snow(
        height=args.height,
        width=args.width,
        intensity=args.intensity,
    )

    # controls the running of the program (exits when false)
    running = True
    tick_rate_ms = args.tick_rate_ms
    help_text = "[0-9]: set intensity\ni: increase intensity\nd: decrease intensity\nx: exit simulation\nh: toggle this help"
    display_help = True

    def snow_simulation():
        nonlocal snow
        nonlocal tick_rate_ms
        while running:
            snow.update_flakes()
            os.system("clear")
            print(snow.render())
            if display_help:
                print(help_text)
            # print(f"{self.tick // 10} {len(self.flakes)}")
            time.sleep(tick_rate_ms / 1000)

    # Allow the snow object to be modified within the input handler thread
    def user_input_handler():
        nonlocal snow
        nonlocal running
        nonlocal display_help
        while running:
            user_input = input()
            match user_input:
                case "x":
                    running = False
                case "i":
                    snow.intensity = min(snow.intensity + 1, 10)
                case "d":
                    snow.intensity = max(snow.intensity - 1, 0)
                case "h":
                    display_help = not display_help
                case _ if len(user_input) == 1 and re.match(r"[0-9]", user_input):
                    snow.intensity = int(user_input)

    threading.Thread(target=snow_simulation).start()
    threading.Thread(target=user_input_handler).start()


if __name__ == "__main__":
    main()
