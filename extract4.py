import subprocess, re, json, os, concurrent.futures as cf

def page_col_lines(path):
    out = subprocess.run(['pdftotext','-bbox','-enc','UTF-8',path,'-'],
                         capture_output=True, text=True, timeout=180).stdout
    pages=[]
    for p in out.split('<page')[1:]:
        m=re.search(r'width="([\d.]+)"',p); W=float(m.group(1)) if m else 595.0
        words=[]
        for wm in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', p, re.S):
            x0,y0,x1,y1=map(float,wm.groups()[:4]); t=wm.group(5)
            t=(t.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
                 .replace('&quot;','"').replace('&apos;',"'").replace('&#39;',"'"))
            words.append((y0,x0,x1,t))
        if not words: pages.append([]); continue
        mid = W*0.45
        cols={'L':[w for w in words if w[1]<mid], 'R':[w for w in words if w[1]>=mid]}
        lines=[]
        for cname in ['L','R']:
            ws=sorted(cols[cname])
            cur=[]; cy=None
            for y0,x0,x1,t in ws:
                if cy is None or abs(y0-cy)>3.5:
                    if cur: lines.append((cname,cur))
                    cur=[(x0,t)]; cy=y0
                else: cur.append((x0,t))
            if cur: lines.append((cname,cur))
        pages.append([(c, ' '.join(t for _,t in sorted(ws))) for c,ws in lines])
    return pages

def doc(path):
    seq=[]
    for pi,pg in enumerate(page_col_lines(path)):
        for c,t in pg: seq.append((pi,c,t))
    return seq

def block(seq, label_re, col_stop=True, maxn=60):
    for i,(pi,c,t) in enumerate(seq):
        if re.search(label_re, t):
            out=[]
            for pi2,c2,t2 in seq[i+1:i+1+maxn]:
                if pi2!=pi and c2!=c: pass
                if col_stop and pi2==pi and c2!=c: break
                if pi2>pi+1: break
                out.append(t2)
            return out
    return []

if __name__=='__main__':
    import sys
    for sid in sys.argv[1:]:
        print('='*10,sid)
        print('\n'.join(block(doc(f'data/pdf/{sid}.pdf'), r'學校關注事項[：:]'))[:500])
