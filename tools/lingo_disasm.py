import sys, struct
sys.path.insert(0, '/home/runner/game/mizube-renpy/tools')
from to_renpy import Rifx

SINGLE = {0x00:'invalid',0x01:'ret',0x02:'retFactory',0x03:'pushZero',0x04:'mul',0x05:'add',0x06:'sub',0x07:'div',0x08:'mod',0x09:'inv',0x0a:'joinStr',0x0b:'joinPadStr',0x0c:'lt',0x0d:'ltEq',0x0e:'ntEq',0x0f:'eq',0x10:'gt',0x11:'gtEq',0x12:'and',0x13:'or',0x14:'not',0x15:'containsStr',0x16:'contains0Str',0x17:'getChunk',0x18:'hiliteChunk',0x19:'ontoSpr',0x1a:'intoSpr',0x1b:'getField',0x1c:'startTell',0x1d:'endTell',0x1e:'pushList',0x1f:'pushPropList',0x21:'swap',0x26:'callJavaScript'}
MULTI = {0x41:'pushInt8',0x42:'pushArgListNoRet',0x43:'pushArgList',0x44:'pushCons',0x45:'pushSymb',0x46:'pushVarRef',0x48:'getGlobal2',0x49:'getGlobal',0x4a:'getProp',0x4b:'getParam',0x4c:'getLocal',0x4e:'setGlobal2',0x4f:'setGlobal',0x50:'setProp',0x51:'setParam',0x52:'setLocal',0x53:'jmp',0x54:'endRepeat',0x55:'jmpIfZ',0x56:'localCall',0x57:'extCall',0x58:'objCallV4',0x59:'put',0x5a:'putChunk',0x5b:'deleteChunk',0x5c:'get',0x5d:'set',0x5f:'getMovieProp',0x60:'setMovieProp',0x61:'getObjProp',0x62:'setObjProp',0x63:'tellCall',0x64:'peek',0x65:'pop',0x66:'theBuiltin',0x67:'objCall',0x6d:'pushChunkVarRef',0x6e:'pushInt16',0x6f:'pushInt32',0x70:'getChainedProp',0x71:'pushFloat32',0x72:'getTopLevelProp',0x73:'newObj'}

def disasm(code, names, globals_names=None, locals_names=None):
    out = []
    i = 0
    n = len(code)
    while i < n:
        pos = i
        op = code[i]; i += 1
        raw = op
        mnem = None; arg = None; arglen = 0
        if op >= 0xc0:
            arglen = 4
        elif op >= 0x80:
            arglen = 2
        elif op >= 0x40:
            arglen = 1
        if arglen:
            argbytes = code[i:i+arglen]
            if raw >= 0xc0:
                arg = struct.unpack('>i', argbytes)[0]
            elif raw >= 0x80:
                mapped = 0x40 + (raw % 0x40)
                if mapped in (0x6e, 0x41):  # pushInt16/pushInt8 -> signed
                    arg = struct.unpack('>h', argbytes)[0]
                else:
                    arg = struct.unpack('>H', argbytes)[0]
            else:
                if 0x40 + (raw % 0x40) == 0x41:
                    arg = struct.unpack('>b', argbytes)[0]
                else:
                    arg = argbytes[0]
            i += arglen
            mnem = MULTI.get(0x40 + (raw % 0x40), f'op{0x40 + (raw % 0x40):02x}')
        else:
            mnem = SINGLE.get(op, f'op{op:02x}')
        annot = ''
        if mnem in ('extCall','pushSymb','localCall') and arg is not None and arg < len(names):
            annot = ' ; ' + names[arg]
        if mnem in ('getGlobal','setGlobal','getGlobal2','setGlobal2') and arg is not None:
            annot = ' ; ' + (names[arg] if arg < len(names) else f'g{arg}')
        if mnem == 'jmp' or mnem == 'jmpIfZ':
            annot = f' ; -> {pos + arg}'
        out.append(f'  {pos:4d}: {mnem} {"" if arg is None else arg}{annot}')
    return '\n'.join(out)

def parse_lnam(buf):
    off, cnt = struct.unpack_from('>HH', buf, 16)
    pos = off
    names = []
    for _ in range(cnt):
        l = buf[pos]
        names.append(buf[pos+1:pos+1+l].decode('mac-roman'))
        pos += 1 + l
    return names

def get_handler(rifx, lctx, member, hidx=0, lnam_body=231986):
    lctx = rifx.body(rifx.find(b'LctX')[0])
    unknown0, section_id, u1, u2 = struct.unpack_from('>IiHH', lctx, 96 + (member-1)*12)
    sec = rifx.body(section_id)
    handlers_count, handlers_offset = struct.unpack_from('>HI', sec, 72)
    rec = sec[handlers_offset + hidx*40 : handlers_offset + hidx*40 + 40]
    nid, vpos, clen, coff = struct.unpack_from('>HHII', rec, 0)
    return sec[coff:coff+clen], rifx.body(lnam_body), nid

if __name__ == '__main__':
    r = Rifx('/home/runner/game/RE227368/system.cxt')
    for member in (9, 48):
        code, lnambuf, nid = get_handler(r, None, member)
        names = parse_lnam(lnambuf)
        print(f'=== system member {member} handler "{names[nid]}" ({len(code)} bytes):')
        print(disasm(code, names))
