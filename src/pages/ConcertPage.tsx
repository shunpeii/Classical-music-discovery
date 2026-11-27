import type {ReactNode} from 'react';
import type {Era,Composer,Work,Concert} from '../types';
type Props={concert:Concert;go:(r:string)=>void;price:(c:Concert)=>string;toggle:(id:string)=>void;id:string;saved:string[];workRows:(items:Work[])=>ReactNode;works:Work[]};
export function ConcertPage({concert,go,price,toggle,id,saved,workRows,works}:Props){return <><button onClick={()=>go('concerts')}>← 公演一覧</button><h1>{concert.title}</h1><p>{concert.date} · {concert.venue}</p><p>{price(concert)}</p>{concert.sourceUrl&&<p><a href={concert.sourceUrl} target="_blank" rel="noreferrer">公式公演情報・チケット ↗</a></p>}<button onClick={()=>toggle(id)}>{saved.includes(id)?'♥ 保存済み':'♡ 保存する'}</button><h2>演奏曲</h2>{workRows(works.filter(w=>concert.workIds.includes(w.id)))}</>;}
