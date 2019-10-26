import argparse
import os.path
import datetime
from typing import List, Dict, Any

from parse_log import parse_log
from stats import get_stats_from_sessions, Stats
from top_list import TopList
from title_info import get_title


def trim_microseconds(td: datetime.timedelta) -> datetime.timedelta:
    return td - datetime.timedelta(microseconds=td.microseconds)


def print_bar_chart(
    top_list: List[Stats], criteria: str, bar_length: int, list_length: int
):
    f = None
    if criteria == "total" or criteria is None:

        def g(x):
            r = x.get_total_time_played()
            return r, str(datetime.timedelta(seconds=r))

        f = g
    elif criteria == "times":

        def g(x):
            r = x.get_times_played()
            return r, str(r)

        f = g
    elif criteria == "average":

        def g(x):
            r = x.get_average_session_time()
            return r, str(trim_microseconds(datetime.timedelta(seconds=r)))

        f = g
    elif criteria == "median":

        def g(x):
            r = x.get_median_session_time()
            return r, str(datetime.timedelta(seconds=r))

        f = g

    max_value = max(f(g)[0] for g in top_list[:list_length])
    increment = max_value / bar_length
    longest_label_length = max(
        len(get_title(g.get_game(), g.get_system())) for g in top_list[:list_length]
    )
    longest_value_length = max(len(f(g)[1]) for g in top_list[:list_length])

    for g in top_list[:list_length]:
        value, value_string = f(g)
        bar_chunks, remainder = divmod(int(value * 8 / increment), 8)
        bar = "█" * bar_chunks
        title = get_title(g.get_game(), g.get_system())
        if remainder > 0:
            bar += chr(ord("█") + (8 - remainder))
        bar = bar or "▏"
        print(
            "{} ▏ {} {}".format(
                title.rjust(longest_label_length),
                value_string.rjust(longest_value_length),
                bar,
            )
        )


def print_list_entries(top_list: List[Stats], length: int):
    for i, g in enumerate(top_list[:length], start=1):
        list_entry = (
            "{} for {}, played {} times, " "time played: {}, avg: {}, median: {}"
        )
        title = get_title(g.get_game(), g.get_system())

        list_entry = list_entry.format(
            title,
            g.get_system(),
            g.get_times_played(),
            datetime.timedelta(seconds=g.get_total_time_played()),
            trim_microseconds(datetime.timedelta(seconds=g.get_average_session_time())),
            datetime.timedelta(seconds=g.get_median_session_time()),
        )
        print(i, list_entry)


def parse_args() -> Dict[str, Any]:
    desc = "Calculate some play statistics for your retro gaming"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-n",
        "--list-length",
        type=int,
        default=25,
        help="how many entries to print int the top list",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default="/home/pi/RetroPie/game_stats.log",
        help="path to the stats file",
    )
    parser.add_argument(
        "-c",
        "--criteria",
        type=str,
        default=None,
        help="which criteria to order by, available options "
        "are: total (time), times (played), "
        "average (session length), "
        "median (session length), "
        "defaults to total",
    )
    parser.add_argument(
        "-s",
        "--system",
        type=str,
        default=None,
        help="the system you want statistics for, if omitted, will use all systems",
    )
    parser.add_argument(
        "-m",
        "--minimum-session-length",
        type=int,
        default=120,
        help="skip sessions shorter than this number of seconds, defaults to 120",
    )
    parser.add_argument(
        "-b",
        "--bar-chart",
        type=int,
        help="display bar chart instead of numbers, integer sets bar length",
    )
    parser.add_argument(
        "-e",
        "--exclude-systems",
        type=str,
        default=None,
        nargs="+",
        help="skip the listed systems, only respected if --system is unset",
    )

    return vars(parser.parse_args())


def main():
    args = parse_args()

    sessions = {}
    sessions = parse_log(args["file"], args["minimum_session_length"])
    stats = get_stats_from_sessions(sessions)
    top = TopList(stats)

    sys = args["system"]
    excl_sys = args["exclude_systems"]
    criteria = args["criteria"]
    top_list = []
    if criteria == "total" or criteria is None:
        top_list = top.get_top_total_time(sys, excl_sys)
    elif criteria == "times":
        top_list = top.get_top_times_played(sys, excl_sys)
    elif criteria == "average":
        top_list = top.get_top_average(sys, excl_sys)
    elif criteria == "median":
        top_list = top.get_top_median(sys, excl_sys)

    if not args["bar_chart"] is None:
        print_bar_chart(
            top_list,
            criteria if args["bar_chart"] else None,
            args["bar_chart"],
            args["list_length"],
        )
    else:
        print_list_entries(top_list, args["list_length"])


if __name__ == "__main__":
    main()
