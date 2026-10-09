"""Serialize body exchanges and extra form/costume reloads for one match.

An acknowledged extra form transaction must finish first. Once Body Change
captures its pair, no new extra resource IO starts until that pair is released.
The same extra worker survives a body exchange: it owns loaded resource receipts
and must not forget them while its native stage remains installed.
"""


def attach_body(p, progress=None, **options):
    """Attach the serial body worker; options are Worker keyword arguments
    (for example stuck_frames, or injected read_ram/apply/quiet/resume)."""
    import body_swap_worker
    worker = body_swap_worker.Worker(progress=progress, **options)
    if p.read_u32(body_swap_worker.body.CONTROL)==0:
        worker.attach(p)
        return worker
    native=body_swap_worker.native
    held=p.read_u32(native.CONTROL+16)==1 and p.read_u32(native.CONTROL+20)==1
    if not held:worker.quiet(p)
    # Failure is terminal: never release an uncertain installation or claim.
    worker.attach(p)
    if not held:worker.resume(p)
    return worker


def attach_fusion(p, progress=None, **options):
    """Claim the optional duration service under the native preparation hold."""
    import fusion_duration_worker as duration
    if p.read_u32(duration.timer.CONTROL)==0:
        return None
    worker=duration.Worker(progress=progress, **options)
    held=p.read_u32(duration.native.CONTROL+16)==1 and p.read_u32(duration.native.CONTROL+20)==1
    if not held:worker.quiet(p)
    worker.attach(p)
    if not held:worker.resume(p)
    return worker


def poll(p, extra, body, fusion=None):
    if extra.failure:
        raise RuntimeError(extra.failure)
    if body is not None and body.failure:
        raise RuntimeError(body.failure)
    if fusion is not None and fusion.failure:
        raise RuntimeError(fusion.failure)
    if extra.form_job is not None:
        extra.poll(p)
    else:
        if fusion is not None:
            fusion.poll(p,reload_worker=extra,body_worker=body)
            if fusion.failure:
                raise RuntimeError(fusion.failure)
            if fusion.busy:return
        if body is not None:
            body.poll(p, reload_worker=extra)
            if body.failure:
                raise RuntimeError(body.failure)
        if body is None or not body.busy:
            extra.poll(p)
    if extra.failure:
        raise RuntimeError(extra.failure)


def poll_delay(extra,body,fusion,ordinary):
    """Short sleeps only while a serial guest transaction needs acknowledgement.

    An extra's transformation disc read now runs unheld for well over a second
    with combat dispatching normally. Polling that at10ms would open ~170 PINE
    cycles, each with a full preflight, during live play; the acknowledgement
    that really needs a short sleep only begins once the row reaches3/4.
    """
    if extra is not None and getattr(extra,'form_phase',None)=='io':
        return min(ordinary,.05)
    busy=(extra is not None and extra.form_job is not None) or any(
        worker is not None and worker.busy for worker in (body,fusion))
    return min(ordinary,.01) if busy else ordinary
