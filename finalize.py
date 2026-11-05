import json, re, concurrent.futures as cf
from extract4 import doc

HEADS=['學校管理架構','法團校董會','環保政策','全校語文政策','學習和教學策略','課外閱讀計劃',
 '校本課程','學校課程主要更新重點','生涯規劃教育','全校參與照顧學生的多樣性','全校參與模式融合教育',
 '非華語學生的教育支援','測考及學習調適措施','學費減免','校風','家校合作','教師專業培訓及發展',
 '學校發展計劃','學校設施','全方位學習','家長教師會','學生會','辦學宗旨','未來發展','學校特色',
 '學校管理','教學規劃','學生支援','學校生活','開設科目']

NUM = (r'(?:關注事項\s*[一二三四五六七八九十\d]+\s*[\.、：:]?'
       r'|(?:I{1,3}|IV)\.?\d{1,2}'
       r'|[\(（]\s*\d{1,2}\s*[\)）]'
       r'|\d{1,2}\s*[\.、\)）]'
       r'|[一二三四五六七八九十]{1,2}\s*[、\.])')

def is_head(t):
    t=t.strip()
    if len(t)>26: return False
    return any(t.startswith(h) for h in HEADS) and (t.endswith('：') or len(t)<=len(h)+4)

def parse(path):
    seq=doc(path)
    for i,(pi,c,t) in enumerate(seq):
        if re.search(r'學校關注事項[：:]', t):
            lines=[]
            for pi2,c2,t2 in seq[i+1:i+55]:
                if pi2>pi+1: break
                if pi2==pi and c2!=c: break
                tt=t2.strip()
                if is_head(tt):
                    if ('關注項目' in tt or '重點關注' in tt):
                        tt=re.sub(r'^.*?[：:]','',tt).strip()
                        if tt: lines.append(tt)
                        continue
                    break
                lines.append(tt)
            return lines
    return []

def logical(lines):
    out=[]
    for l in lines:
        if out and not re.match('^'+NUM, l) and not re.search(r'[。；;]$', out[-1]):
            out[-1]+=l
        else:
            out.append(l)
    return out

def split_num(s):
    marks=[m.start() for m in re.finditer(NUM, s)]
    if not marks: return [s]
    items=[]
    if marks[0]>0: items.append(s[:marks[0]])
    for a,b in zip(marks, marks[1:]): items.append(s[a:b])
    items.append(s[marks[-1]:])
    return items

def strip_num(s):
    s=re.sub('^'+NUM, '', s)
    return s.strip(' ；;，,、：:')

THEME_RE=re.compile(r'^(?:本校)?(?:20\d\d[-–]\d{2,4}\s*)?(?:學年)?(?:三年)?(?:發展計劃)?(?:的)?(?:主題|口號)[：:為]?\s*(.+)$')

def clean(parts):
    out=[]; theme=''
    for s in parts:
        s=re.sub(r'\s+',' ',s).strip()
        if not s: continue
        m=THEME_RE.match(s)
        if m and len(m.group(1))<60:
            theme=m.group(1).strip(' 。'); continue
        for h in HEADS:
            i=s.find(h+'：')
            if i>0: s=s[:i]
        s=strip_num(s)
        if len(s)<4: continue
        if re.fullmatch(r'[-－—–‐\s\.]+', s): continue
        out.append(s)
    merged=[]
    for s in out:
        if merged and len(merged[-1])<6:
            merged[-1]+=s
        else: merged.append(s)
    seen=set(); res=[]
    for s in merged:
        k=s[:14]
        if k in seen: continue
        seen.add(k); res.append(s)
    return theme, res

d=json.load(open('data/schools_raw.json'))
def work(s):
    sid=s['sch_id']
    try:
        lines=parse(f'data/pdf/{sid}.pdf')
        parts=[]
        for L in logical(lines): parts+=split_num(L)
        theme,items=clean(parts)
    except Exception as e:
        theme,items='',['ERR '+str(e)]
    return sid, dict(theme=theme, items=items)

res={}
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for sid,v in ex.map(work,d): res[sid]=v
json.dump(res, open('data/final_concerns.json','w'), ensure_ascii=False, indent=1)
import collections
print('no items', sum(1 for v in res.values() if not v['items']))
print(collections.Counter(len(v['items']) for v in res.values()))
print('themes', sum(1 for v in res.values() if v['theme']))
