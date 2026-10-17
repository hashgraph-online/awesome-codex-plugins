// Independent read-only checks may overlap. On failure, stop assigning work
// and settle every admitted check before the caller releases its owning locks.
export async function boundedRead(items, concurrency, read) {
  if(!Number.isSafeInteger(concurrency)||concurrency<1)throw new RangeError('Read concurrency must be a positive integer');
  const results=new Array(items.length),errors=[];let next=0;
  const workers=Array.from({length:Math.min(concurrency,items.length)},async()=>{
    while(!errors.length&&next<items.length){
      const index=next++;
      try{results[index]=await read(items[index],index);}
      catch(error){errors.push({index,error});}
    }
  });
  const settled=await Promise.allSettled(workers);
  for(const result of settled)if(result.status==='rejected')errors.push({index:items.length,error:result.reason});
  if(errors.length){
    errors.sort((a,b)=>a.index-b.index);
    if(errors.length===1)throw errors[0].error;
    throw Object.assign(new AggregateError(errors.map(x=>x.error),'Independent read checks failed'),{
      code:errors[0].error?.code,
      details:{failed_read_count:errors.length,failures:errors.slice(0,concurrency).map(({index,error})=>({index,
        code:typeof error?.code==='string'?error.code.slice(0,128):null,
        type:error instanceof SyntaxError?'SyntaxError':error instanceof Error?'Error':'NonError'}))},
    });
  }
  return results;
}
