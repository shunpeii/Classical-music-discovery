import {useState} from 'react';
import type {Composer} from '../types';
export function Portrait({composer,detail=false,priority=false}:{composer:Composer;detail?:boolean;priority?:boolean}){
 const src=composer.portrait?new URL(composer.portrait.replace(/^\/+/,''),new URL(import.meta.env.BASE_URL,document.baseURI)).href:undefined;
 const [failedSrc,setFailedSrc]=useState<string>();
 return <div className="composer-photo">{src&&failedSrc!==src?<img key={src} src={src} alt={composer.name} loading={detail||priority?'eager':'lazy'} onError={()=>{console.error('Portrait failed to load:',src);setFailedSrc(src)}}/>:<span>{composer.name.slice(0,1)}</span>}</div>
}
