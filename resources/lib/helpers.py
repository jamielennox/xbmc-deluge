

# in the deluge version the units are localized with _
def fspeed(bps):
    """
    Formats a string to display a transfer speed utilizing :func:`fsize`

    :param bps: bytes per second
    :type bps: int
    :returns: a formatted string representing transfer speed
    :rtype: string

    **Usage**

    >>> fspeed(43134)
    '42.1 KiB/s'

    """
    fspeed_kb = bps / 1024.0
    if fspeed_kb < 1024:
        return "%.1f %s" % (fspeed_kb, "KiB/s")
    fspeed_mb = fspeed_kb / 1024.0
    if fspeed_mb < 1024:
        return "%.1f %s" % (fspeed_mb, "MiB/s")
    fspeed_gb = fspeed_mb / 1024.0
    return "%.1f %s" % (fspeed_gb, "GiB/s")


