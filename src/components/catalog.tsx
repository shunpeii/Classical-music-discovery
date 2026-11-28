import type {Composer,Work,Concert} from '../types';
export function catalog({composers,saved,go,toggle}:{composers:Composer[];works:Work[];saved:string[];go:(r:string)=>void;toggle:(id:string)=>void}){
 const spotify=(w:Work)=>'https://open.spotify.com/search/'+encodeURIComponent((composers.find(c=>c.id===w.composerId)?.name||'')+' '+w.title);
 const price=(c:Concert)=>c.price===null?'料金未定':'¥'+c.price.toLocaleString()+'〜';
 const cards=(items:Concert[])=>items.length?<div className="concert-list">{[...items].sort((a,b)=>a.date.localeCompare(b.date)).map(c=><article key={c.id}><button className="date-tile" onClick={()=>go('concert/'+c.id)}>{Number(c.date.slice(5,7))}/{Number(c.date.slice(8,10))}</button><div className="concert-info"><button className="link heading" onClick={()=>go('concert/'+c.id)}>{c.title}</button><p>⌖ {c.venue}</p><strong>{price(c)}</strong></div><button className="favorite" aria-label="お気に入り" aria-pressed={saved.includes(c.id)} onClick={()=>toggle(c.id)}>{saved.includes(c.id)?'♥':'♡'}</button></article>)}</div>:<p>該当する公演はありません。</p>;
 const workRows=(items:Work[])=>items.map(w=><button className="work-row" key={w.id} onClick={()=>go('work/'+w.id)}><span className="work-thumb">♫</span><strong>{w.title}</strong><span>›</span></button>);

return {spotify,price,cards,workRows};
}
