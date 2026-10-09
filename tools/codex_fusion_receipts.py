"""Retire host receipt authority after verified defusion, never free its RAM."""
def invalidate_restored_partners(extra,event):
    if getattr(extra,'form_job',None) is not None:
        raise RuntimeError('Extra form transaction still owns its acknowledgment')
    physical=event['physical_ids']
    old_ids=list(event['old_resources'])
    details=handoff_summary(event)
    if len(physical)!=2 or any(type(value) is not int or not 0<=value<10 for value in physical+old_ids):
        raise ValueError(f'Invalid defusion physical IDs: {details}')
    if len(set(physical))!=2:
        raise ValueError(f'Duplicate defusion partners: {details}')
    if event['new_resources']:
        raise ValueError(f'Defusion unexpectedly transfers new resource ownership: {details}')
    # Defusion rebuilds only the leader via a resource configuration; the
    # retained partner has a separate verified restoration plan. Consequently
    # old_resources normally contains ONE ID, while physical_ids contains two.
    # Quarantine the union, including any extra captured configuration owner.
    restored=sorted(set(physical)|set(old_ids))
    # Restored initial bundles are not transformation-owned allocations. Do
    # not mint a new receipt for them or free/rebase the superseded receipt.
    # Preserve ambiguous metadata for diagnostics but exclude it from retirement.
    quarantine=getattr(extra,'fusion_receipt_quarantine',None)
    if quarantine is None:quarantine=[];extra.fusion_receipt_quarantine=quarantine
    count=0
    for slot in restored:
        active=extra.resources.pop(slot,None)
        pending=extra.retained.pop(slot,[])
        for kind,receipts in (('active',[active] if active is not None else []),('pending',pending)):
            for receipt in receipts:
                quarantine.append(dict(generation=event['generation'],physical=slot,kind=kind,receipt=receipt))
                count+=1
    if count:
        extra.retirement_notes.append(f'Defusion invalidated {count} prior transformation receipts for restored partners {restored}; no old bundle freed')
    return count


def handoff_summary(event):
    return (f"generation={event['generation']} physical_ids={event['physical_ids']!r} "
            f"old_resources={event['old_resources']!r} new_resources={event['new_resources']!r} "
            f"bodies={event.get('bodies', [])!r}")
