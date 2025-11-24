"""Disc-related helpers also useful elsewhere in ARver."""


def frames_to_msf(frames: int) -> str:
    """Convert integer number of CD frames to time as mm:ss.ff string."""
    frames_per_second = 75

    if frames < 0:
        raise ValueError(f'Negative frames: {frames}')

    min_ = frames // frames_per_second // 60
    sec = frames // frames_per_second % 60
    frm = frames % frames_per_second
    return f'{min_}:{sec:02d}.{frm:02d}'
