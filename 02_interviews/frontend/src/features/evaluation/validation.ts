export function hasCompleteScores(categories:Array<{name:string}>, scores:Record<string,{rating?:number;rationale?:string}>){
  return categories.every(category=>Boolean(scores[category.name]?.rating)&&Boolean(scores[category.name]?.rationale?.trim()));
}
