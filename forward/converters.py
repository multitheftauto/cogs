import logging
import re
from typing import Union, Dict
from datetime import timedelta

from discord.ext.commands.converter import Converter
from redbot.core import commands
from redbot.core import i18n

log = logging.getLogger("red.cogs.forward")

# the following regex is slightly modified from Red
# it's changed to be slightly more strict on matching with finditer
# this is to prevent "empty" matches when parsing the full reason
# This is also designed more to allow time interval at the beginning or the end of the mute
# to account for those times when you think of adding time *after* already typing out the reason
# https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/commands/converter.py#L55
TIME_RE_STRING = r"|".join(
    [
        r"((?P<weeks>\d+?)\s?(weeks?|w))",
        r"((?P<days>\d+?)\s?(days?|d))",
        r"((?P<hours>\d+?)\s?(hours?|hrs|hr?))",
        r"((?P<minutes>\d+?)\s?(minutes?|mins?|m(?!o)))",  # prevent matching "months"
        r"((?P<seconds>\d+?)\s?(seconds?|secs?|s))",
    ]
)
TIME_RE = re.compile(TIME_RE_STRING, re.I)
TIME_SPLIT = re.compile(r"t(?:ime)?=")

_ = i18n.Translator("Forward", __file__)

def str_to_timedelta(
    duration: str
) -> Dict[str, Union[timedelta, str, None]]:
    time_split = TIME_SPLIT.split(duration)
    result: Dict[str, Union[timedelta, str, None]] = {}
    if time_split:
        maybe_time = time_split[-1]
    else:
        maybe_time = duration

    time_data = {}
    for time in TIME_RE.finditer(maybe_time):
        duration = duration.replace(time[0], "")
        for k, v in time.groupdict().items():
            if v:
                time_data[k] = int(v)
    if time_data:
        try:
            result["duration"] = timedelta(**time_data)
        except OverflowError:
            raise commands.BadArgument(
                _("The time provided is too long; use a more reasonable time.")
            )
    result["reason"] = duration.strip()
    return result