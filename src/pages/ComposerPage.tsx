import type {ReactNode} from 'react';
import type {Era,Composer,Work,Concert} from '../types';
type Props={composer:Composer;setEra:(s:string)=>void;go:(r:string)=>void;workRows:(items:Work[])=>ReactNode;works:Work[];id:string;cards:(items:Concert[])=>ReactNode;concerts:Concert[]};
export function ComposerPage({composer,setEra,go,workRows,works,id,cards,concerts}:Props){return <><button onClick={()=>{setEra(composer.eraId);go('history')}}>← 音楽史</button><h1>{composer.name}</h1><p>{composer.birth}–{composer.death}</p><h2>代表曲</h2>{workRows(works.filter(w=>w.composerId===id))}<h2>関連公演</h2>{cards(concerts.filter(c=>c.workIds.some(w=>works.some(x=>x.id===w&&x.composerId===id))))}</>;}
