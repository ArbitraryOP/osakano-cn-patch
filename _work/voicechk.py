import sys, io, traceback
sys.path.insert(0, r'E:\game\_work\agentA')
import lax
sys.stdout = io.open(r'E:\game\_work\voicechk_out.txt','w',encoding='utf-8')
path = r'E:\game\osakano\voice.lax'   # ASCII junction
try:
    res = lax.read_archive(path)
    hdr, ftr, dirblob, entries = res
    print('read_archive OK')
    print('footer:', ftr)
    print('entries:', len(entries))
    for e in entries[:6]:
        print('  ', {k:v for k,v in e.items() if k!='name'}, '|', e.get('name'))
    # check last entry offset+size vs file size
    last = entries[-1]
    print('last entry name=', last.get('name'))
except Exception as ex:
    print('read_archive FAILED:', repr(ex))
    traceback.print_exc()
