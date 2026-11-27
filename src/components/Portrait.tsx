import {useState} from 'react';
import type {Composer} from '../types';
export function Portrait({composer,detail=false,priority=false}:{composer:Composer;detail?:boolean;priority?:boolean}){
 const [failed,setFailed]=useState(false);
 const [fallback,setFallback]=useState(false);
 const original=composer.portrait;
 const source=original&&!fallback&&!detail?original.replace(/\.[^.]+$/,'.thumb.webp'):original;
 return <div className="composer-photo">{source&&!failed?<img src={import.meta.env.BASE_URL+source} alt={composer.name} title="画像出典は images/composers/credits.html を参照" loading={detail||priority?'eager':'lazy'} fetchPriority={detail?'high':'auto'} decoding="async" onError={()=>{if(!fallback&&!detail)setFallback(true);else setFailed(true)}}/>:<span>{composer.name.slice(0,1)}</span>}</div>
}
