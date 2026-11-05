import json, re, glob, os, collections

CONCERN = re.compile(r'(關注事項\s*[（(]?\s*[一二三四五1-5]\s*[)）]?\s*[：:、.]?|關注項目\s*[（(]?\s*[一二三四五1-5]\s*[)）]?\s*[：:、.]?|Major\s+Concern[s]?\s*\d?)', re.I)
OUTCOME = re.compile(r'(成效|成果|預期成果|評估|檢討|反思|達成|表現|Outcome[s]?|Evaluation|Review)', re.I)
NOISE = re.compile(r'(^\s*$|^\d{1,3}\s*$|^[-—_=·\.]+$)')

def clean(t):
    t=t.replace('\u3000',' ')
    t=re.sub(r'[ \t]+',' ',t)
    lines=[l.strip() for l in t.split('\n')]
    lines=[l for l in lines if l and not NOISE.match(l)]
    return lines

def sentences(lines, maxn=3, maxlen=90):
    out=[]
    for l in lines:
        for s in re.split(r'(?<=[。；;！？])', l):
            s=s.strip(' ，,、')
            if len(s)<8: continue
            if len(s)>maxlen: s=s[:maxlen].rstrip('，,')+'…'
            out.append(s)
            if len(out)>=maxn: return out
    return out

def parse(text):
    lines=clean(text)
    joined='\n'.join(lines)
    idx=[m.start() for m in CONCERN.finditer(joined)]
    if not idx: return []
    blocks=[]
    for i,st in enumerate(idx[:5]):
        en=idx[i+1] if i+1<len(idx) else min(len(joined), st+2500)
        chunk=joined[st:en]
        head=chunk.split('\n',1)[0]
        head=CONCERN.sub('',head).strip(' ：:、.')
        body=chunk.split('\n',1)[1] if '\n' in chunk else ''
        bl=clean(body)
        # split content vs outcome
        outc_i=None
        for j,l in enumerate(bl):
            if OUTCOME.search(l) and len(l)<=40: outc_i=j; break
        content_lines=bl[:outc_i] if outc_i is not None else bl
        outcome_lines=bl[outc_i:] if outc_i is not None else []
        blocks.append({
            'title': head[:60] or '關注事項',
            'content': sentences(content_lines, 2, 100),
            'outcome': sentences(outcome_lines, 3, 110),
        })
    # dedupe
    seen=set(); out=[]
    for b in blocks:
        k=b['title'][:12]+b['content'][0][:12] if b['content'] else b['title'][:12]
        if k in seen: continue
        seen.add(k); out.append(b)
    return out

if __name__=='__main__':
    rows={r['id']:r for r in json.load(open('data/schools.json'))}
    idx=json.load(open('data/reports/pdf_index.json'))
    out={}
    for sid,kept in idx.items():
        yrs=[]
        for k in sorted(kept,key=lambda x:x['y']):
            p=f"data/reports/txt/{sid}_{k['y']}.txt"
            if not os.path.exists(p): continue
            blocks=parse(open(p,encoding='utf-8').read())
            if not blocks: continue
            yrs.append({'y':k['y'],'u':k['u'],'b':blocks})
        if yrs: out[sid]=yrs
    json.dump(out,open('data/reports/parsed.json','w'),ensure_ascii=False,indent=1)
    print('schools parsed',len(out),'years',sum(len(v) for v in out.values()))
    print('blocks',sum(len(y['b']) for v in out.values() for y in v))
