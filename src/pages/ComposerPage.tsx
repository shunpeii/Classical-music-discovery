import {useState} from 'react';
import {Portrait} from '../components/Portrait';
import type {ReactNode} from 'react';
import type {Era,Composer,Work,Concert} from '../types';
type Props={composer:Composer;setEra:(s:string)=>void;go:(r:string)=>void;workRows:(items:Work[])=>ReactNode;works:Work[];id:string;cards:(items:Concert[])=>ReactNode;concerts:Concert[]};
export function ComposerPage({composer,setEra,go,workRows,works,id,cards,concerts}:Props){const [tab,setTab]=useState('works');return <><section className="composer-hero"><button className="back" onClick={()=>{setEra(composer.eraId);go('home')}}>←</button><Portrait key={composer.id} composer={composer}/><div><h1>{composer.name}</h1><p>({composer.birth}–{composer.death})</p></div></section><div className="detail-body"><div className="tabs"><button className={tab==='works'?'active':''} onClick={()=>setTab('works')}>代表的な曲</button><button className={tab==='concerts'?'active':''} onClick={()=>setTab('concerts')}>この作曲家の公演</button></div>{tab==='works'?workRows(works.filter(w=>w.composerId===id)):cards(concerts.filter(c=>c.workIds.some(w=>works.some(x=>x.id===w&&x.composerId===id))))}</div></>;}
