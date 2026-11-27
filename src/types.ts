export type Era={id:string;name:string;years:string;description:string;contextTitle?:string;context?:string;sound?:string;headline?:string;story?:string;timeline?:string[];listen?:string};
export type Composer={id:string;name:string;eraId:string;birth:number;death:number;portrait?:string};
export type Work={id:string;composerId:string;title:string;guide?:string};
export type Concert={id:string;title:string;date:string;venue:string;area:string;price:number|null;workIds:string[];mood:string;sourceUrl?:string};
export type Data={eras:Era[];composers:Composer[];works:Work[];concerts:Concert[];sample:boolean};
