"""Disc-related definitions and helpers also useful elsewhere in ARver."""

LEAD_IN_FRAMES = 150
FRAMES_PER_SECOND = 75


def frames_to_msf(frames: int) -> str:
    """Convert integer number of CD frames to time as mm:ss.ff string."""
    min_ = frames // FRAMES_PER_SECOND // 60
    sec = frames // FRAMES_PER_SECOND % 60
    frm = frames % FRAMES_PER_SECOND
    return f'{min_}:{sec:02d}.{frm:02d}'
