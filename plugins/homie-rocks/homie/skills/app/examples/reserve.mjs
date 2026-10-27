import {defineTool} from '@homie-rocks/studio/tools';
export default defineTool({
 name:'reserve',description:'Reserve one place in a server-owned slot',audience:'signed-in',namespace:'capacity',
 inputSchema:{type:'object',properties:{slot:{type:'string',pattern:'^tee-[0-9]{4}$'}},required:['slot'],additionalProperties:false},
 async handler({slot},ctx){
  const row=await ctx.database.getVersioned(slot);
  if(!row)return {ok:false,reason:'Unknown slot'};
  const value=row.value;
  if(value.remaining<1)return {ok:false,reason:'Full'};
  const result=await ctx.database.put(slot,{remaining:value.remaining-1,bookings:[...value.bookings,ctx.caller.id]},{version:row.version});
  return result.ok?{ok:true}:{ok:false,reason:'Taken; refresh availability'};
 }
});
