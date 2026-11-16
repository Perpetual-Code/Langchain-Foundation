### Blueprint 
- pubmed_search  is the first state in the graph, it will get topic and number of results as search query from the overall state,
- the overall state has topic,reports(annotated) and final_report, 
- pubmed_research outputs the title,abstract,conclusions,result for each paper
- the next node is llm analyst, which takes each result from the pubmed_search node and create a analysis with a title,analysis and conclusion(all in under 100-200 words) because as the number of results increase the context for the final report write grows
- the should_call_llm calls the llm_analyst or the research_writer(final node)
- the should_call uses Send but send what??? -> the think where are you sending?-> sending to llm analyst, so I need to create a state for report and the key has to be a list ,that is being send just like in map-reduce for jokes
- Now I have should_call_llm node and its a fan out router node, which uses Send and it sends each report in the pubmed_search results to call_llm node takes overall state and 



The batch list. The Send function needs something to loop over, and that something is a list in OverallState. I'm asking two things: what you call it, and what one item in it is. The name is yours — it just needs to say "list of papers" and not reuse a name that already means something else (your old results key meant one paper's results field, so results for the list would be confusing). The item shape is the real question, and there are two versions. One is the full dict, fields kept apart: title, abstract, conclusions, results as four separate values. The other is the formatted string your function builds now — title and abstract glued into one piece of text. Why it matters: the Send has to hand the Analyst four separate values. From a dict, you pick each field out. From a string, there are no fields to pick — the Analyst gets one blob of text. And your current string only has title and abstract in it at all, so conclusions and results never reach the Analyst in that version.

-> I'll call it pubmed_results and one item in it is a document(which I didn't create yet but this idea evolved), each document starts with a <document>title abstract conclusions results</document>

--------------------------------------------------------------------------------------
Num of results — cap vs count. Same words, two different moments. The cap is the number you ask for — "fetch me 3" — decided before the call, by you, at invoke time. The count is the number you got back — "PubMed returned 2" — known only after the call. The cap is read by pubmed_search; the count is written by it. Your function's max_results=3 is the cap sitting as a default in the code; making it a state key means the caller sets it, like topic. One more thing to notice: if the batch list is in state, the count is just the list's length — so ask who reads the count. If nobody reads it separately, you may not need the key at all.

-> when I said num_results,it meant one thing and one thing only,i.e. number of results from pubmed_search and regarding the max_results you are talking about(from the researcher agent lesson), here the analyst never asks any questions and as soon as send hand the payload with title,abstract,conclusions,results the llm is supposed to analyze this and create a title and analysis 

-----------------------------------
{topic} in the Analyst's prompt. The question is where the Analyst gets topic from. Here's the mechanism: when a node runs via Send, it sees the whole state — the parent's keys plus its own payload, merged together for that call. So topic is there, from the parent, even though the Analyst's own schema only lists the paper's four fields. The schema is a label for what the node expects; the runtime dict carries everything. So the instructions' {topic} works. I asked because this is different from a sub-graph, where only overlapping keys cross — with Send, the full state comes along.

-> Thank you for clearing this and make sure you keep this in your memory so when you create notes at the end of this session(after the pubmed graph is complete) you can add everything I said and got incorrect and your own notes can be included in that file

-----------------

should_call and the Writer. In the jokes notebook, the routing function only ever fans out to the map node; the reduce node runs afterward through a plain edge — the router never picks it. Your sentence says should_call picks the Analyst or the Writer. So the question is: in what situation does it pick the Writer? The obvious candidate is zero papers. But then what does the Writer write from an empty reports list — a "no papers found" note, or should that case go to END instead? The wiring depends on the answer: if the router can return the Writer's name, the Writer has to be in the path map; if it only returns Sends, the Writer is reached by an edge and the router never mentions it.

-> since send loops over a list or something that is iterable(just as a for loop) correct me if there is something,so the end of the loop, the router will call or pass the control to write node, if you have another approach suggest that,but indirectly
-> the writer reads the analyst_reports(which is named as reported with a add reducer ) state from the overall state and based on the analyst reports, the writer or researcher will create the final report 

--------------------------------------------------------
Report model vs the new shape. Your code's Report says the Analyst returns title, abstract, conclusions, results — a structured restatement of the paper, 200–300 words. Your plain-English flow says it returns title, analysis, conclusion — its own short synthesis, 100–200 words. Different fields, different word counts, different jobs. The Writer reads whatever the Analyst returns, so the shape has to be one of them.

-> Analyst will only create title and analysis all within 200 words max, where as the final report from the writer(or suggest what should I call this node) will create a report with title, analysis and final thoughts/conclusion 

Does that clear them up — which one do you want to settle first?