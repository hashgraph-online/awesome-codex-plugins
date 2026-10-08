// Shared by authoring compilation and every Ready-Workflow validation path.
// A generated graph cannot pass by expressing the same copy-through request in
// a different layer or language.
const NEGATIVE_EN=/\b(?:do not|don't|never|without|omit|exclude|avoid|must not|should not|need not|does not need to)\b/i;
const NEGATIVE_ZH=/(?:不要|不得|无需|避免|禁止|不应|不能)/u;

export function hostOwnedAgentField(name){
  return typeof name==='string'&&/(?:^|_)(?:id|ids|path|paths|sha256|hash|hashes|checksum|checksums|token|tokens|index|indices|revision|receipt|receipts|status|created_at|updated_at|timestamp|timestamps|uuid|uuids|nonce|nonces|seed|seeds|encoding|encoded)$/.test(name);
}

export function agentTranscriptionClauses(instructions){
  return String(instructions??'').split(/(?:[\r\n]+|(?<=[.!?;。！？；]))/u)
    .map(clause=>clause.trim()).filter(clause=>{
      if(!clause||NEGATIVE_EN.test(clause)||NEGATIVE_ZH.test(clause))return false;
      const identityCopy=/\b(?:return|report|emit|output|include|list|cite|record|reproduce|copy|transcribe|provide|supply)\b[\s\S]{0,180}\b(?:exact\s+)?(?:[A-Za-z0-9_-]+\s+)?(?:ids?|paths?|sha(?:-?256)?|hash(?:es)?|checksums?|tokens?|indices|indexes|revisions?|receipts?|timestamps?|uuids?|nonces?|seeds?|encodings?)\b/i;
      const directCopy=/\b(?:copy|transcribe|reproduce|echo|relay|repeat|re-?emit|re-?serialize|pass\s+through|carry\s+forward)\b[\s\S]{0,240}\b(?:inputs?|upstream|sources?|supplied|provided|existing|original|records?|fields?|values?|data|metadata|rows?|items?|content|text|files?|labels?|names?)\b/i;
      const suppliedReturn=/\b(?:return|report|emit|output|include|record|provide|supply)\b[\s\S]{0,160}\b(?:the\s+)?(?:input|upstream|source|supplied|provided|existing|original|manifest|record)(?:'s)?\s+(?:ids?|paths?|hash(?:es)?|tokens?|indices|revisions?|receipts?|timestamps?|fields?|values?|labels?|names?|metadata|text|content)\b/i;
      const unchangedReturn=/\b(?:return|report|emit|output|include|record|provide|supply)\b[\s\S]{0,240}\b(?:verbatim|unchanged|unmodified|same\s+value|as[- ]received|as[- ]supplied|as[- ]provided|from\s+(?:the\s+)?(?:input|upstream|source|manifest|record))\b/i;
      const preserveInput=/\b(?:preserve|retain|keep|forward|propagate|carry)\b[\s\S]{0,160}\b(?:input|upstream|supplied|provided|existing|original|record)(?!\s+(?:order|ordering)\b)[\s\S]{0,120}\b(?:in|into|as|through|to)\s+(?:the\s+)?(?:output|result|response|returned\s+record)\b/i;
      const assignFromInput=/\b(?:set|assign|populate|fill|map|write)\b[\s\S]{0,180}\b(?:output|result|response|field|value)\b[\s\S]{0,120}\b(?:from|to|with|using)\b[\s\S]{0,120}\b(?:input|upstream|source|supplied|provided|existing|original|record)\b/i;
      const deterministicSelection=/\b(?:return|report|emit|output|provide|select|choose|pick)\b[\s\S]{0,160}\b(?:final|latest|last|first|applicable|successful|accepted|selected)\b[\s\S]{0,180}\b(?:result|value|record|review|metadata)?\s*(?:from|among|of)\b[\s\S]{0,180}\b(?:input|upstream|prior|previous|initial|repaired|review|metadata|result|record)[A-Za-z0-9_-]*\b/i;
      const chineseCopy=/(?:复制|抄写|照抄|回填|复述|转录|转交|原样(?:返回|输出)|重新输出)[\s\S]{0,120}(?:输入|上游|来源|已有|原始|记录|字段|值|数据|元数据|文本|内容|ID|标识|路径|哈希|令牌|索引|版本|回执|名称|标签)/u;
      const chineseReturn=/(?:返回|输出|包含|提供)[\s\S]{0,100}(?:输入|上游|来源|已有|原始|记录|提供的)[\s\S]{0,80}(?:字段|值|ID|标识|路径|哈希|令牌|索引|版本|回执|名称|标签|文本|内容|元数据)/u;
      const chinesePreserve=/(?:保留|保持|携带|带入|传递)[\s\S]{0,100}(?:输入(?!顺序)|上游|已有|原始(?!顺序)|记录)[\s\S]{0,100}(?:写入|放入|带入|包含于|保留在)[\s\S]{0,60}(?:输出|结果|响应|返回记录|字段)/u;
      const chineseAssign=/(?:将|把)[\s\S]{0,120}(?:输入|上游|来源|已有|原始|记录|提供的)[\s\S]{0,120}(?:填入|写入|放入|映射到|设为)[\s\S]{0,80}(?:输出|结果|响应|字段|值)/u;
      return identityCopy.test(clause)||directCopy.test(clause)||suppliedReturn.test(clause)||unchangedReturn.test(clause)||preserveInput.test(clause)||assignFromInput.test(clause)||deterministicSelection.test(clause)||chineseCopy.test(clause)||chineseReturn.test(clause)||chinesePreserve.test(clause)||chineseAssign.test(clause);
    });
}

export function firstAgentTranscriptionClause(instructions){
  return agentTranscriptionClauses(instructions)[0];
}
