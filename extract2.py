import subprocess, re

def page_lines(path):
    out = subprocess.run(['pdftotext','-bbox','-enc','UTF-8',path,'-'],
                         capture_output=True, text=True, timeout=120).stdout
    pages=[]
    for p in out.split('<page')[1:]:
        m=re.search(r'width="([\d.]+)"',p); W=float(m.group(1)) if m else 595.0
        words=[]
        for wm in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', p, re.S):
            x0,y0,x1,y1=map(float,wm.groups()[:4]); t=wm.group(5)
            t=(t.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
                 .replace('&quot;','"').replace('&apos;',"'").replace('&#39;',"'"))
            words.append((y0,x0,x1,t))
        words.sort()
        lines=[]; cur=[]; cy=None
        for y0,x0,x1,t in words:
            if cy is None or abs(y0-cy)>3.2:
                if cur: lines.append(cur)
                cur=[(x0,x1,t)]; cy=y0
            else: cur.append((x0,x1,t))
        if cur: lines.append(cur)
        out_lines=[]
        for ln in lines:
            ln.sort()
            out_lines.append((ln[0][0], ' '.join(t for _,_,t in ln)))
        pages.append((W,out_lines))
    return pages

def text_plain(path):
    return subprocess.run(['pdftotext','-enc','UTF-8',path,'-'],capture_output=True,text=True).stdout
