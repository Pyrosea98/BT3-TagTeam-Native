"""Power Scale physical DLC reads while retaining native logical character IDs."""
FIRST, LAST = 10*165+1424, 10*252+1433
DLC_VOLUME = 4


def transport_file_id(file_id):
    if not FIRST <= file_id <= LAST:
        return file_id
    character, section = divmod(file_id-1424, 10)
    index = 26*character-4290+(12 if section==9 else section)
    return (DLC_VOLUME<<24)|index


def emit_transport_file_id(a, value, scratch, character, section, label):
    """Same resolver for a queued runtime ID; caller supplies distinct temporaries."""
    a.li(scratch,FIRST);a.r(0x2B,scratch,value,scratch);a.branch(5,scratch,0,label+'done')
    a.li(scratch,LAST+1);a.r(0x2B,scratch,value,scratch);a.branch(4,scratch,0,label+'done')
    a.addiu(value,value,-1424);a.addiu(scratch,0,10)
    a.r(0x1B,0,value,scratch);a.r(0x12,character,0);a.r(0x10,section,0)
    a.r(0,value,0,character,4);a.r(0,scratch,0,character,3);a.r(0x21,value,value,scratch)
    a.r(0,scratch,0,character,1);a.r(0x21,value,value,scratch);a.addiu(value,value,-4290)
    a.addiu(scratch,0,9);a.branch(5,section,scratch,label+'section')
    a.addiu(section,0,12);a.label(label+'section');a.r(0x21,value,value,section)
    a.li(scratch,DLC_VOLUME<<24);a.r(0x25,value,value,scratch);a.label(label+'done')
