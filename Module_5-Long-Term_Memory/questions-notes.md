### Questions
difference between InMemoryStore() vs MemorySaver()
when storing objects,with namespace,key and value , the key is that only for that particular value? what if there are more values or values get added to the in memory store




### Notes
1. `existing_memory_content = existing_memory.value.get("memory")` in this code, the name `memory` has nothing to do with the name used in the namespace, this name refers to the key `memory` 
   which is used to store the chat history using `put` ->store.put(namespace, key, {"memory": response})
2. 



