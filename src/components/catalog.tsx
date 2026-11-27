import type {Composer,Work,Concert} from '../types';
export function catalog({composers,works,saved,go,toggle}:{composers:Composer[];works:Work[];saved:string[];go:(r:string)=>void;toggle:(id:string)=>void}){
 const spotify=(w:Work)=>'https://open.spotify.com/search/'+encodeURIComponent((composers.find(c=>c.id===w.composerId)?.name||'')+' '+w.title);
 const price=(c:Concert)=>c.price===null?'料金未定':'¥'+c.price.toLocaleString()+'〜';
 const cards=(items:Concert[])=>items.length?<div className="cards">{[...items].sort((a,b)=>a.date.localeCompare(b.date)).map(c=><article key={c.id}><div className="date">{c.date} · {c.area}</div><button className="link heading" onClick={()=>go('concert/'+c.id)}>{c.title}</button><p>{c.venue}</p><div className="line"><strong>{price(c)}</strong><button aria-label="お気に入り" aria-pressed={saved.includes(c.id)} onClick={()=>toggle(c.id)}>{saved.includes(c.id)?'♥':'♡'}</button></div>{works.filter(w=>c.workIds.includes(w.id)).map(w=><a key={w.id} href={spotify(w)} target="_blank" rel="noreferrer">▷ 曲を聴く ↗</a>)}</article>)}</div>:<p>該当する公演はありません。</p>;
 const workRows=(items:Work[])=>items.map(w=><article className="line" key={w.id}><button className="link" onClick={()=>go('work/'+w.id)}>{w.title} →</button><a href={spotify(w)} target="_blank" rel="noreferrer">▷ 試聴</a></article>);

return {spotify,price,cards,workRows};
}
