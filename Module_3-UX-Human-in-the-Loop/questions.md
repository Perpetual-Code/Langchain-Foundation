In some graph.invokes its directly invoke  and in some it is invoke with {"messages":input}
graph1.update_state(input_thread_1, {"messages": user_input}, as_node="human_feedback"), what is as_node parameter here 
In the editing-state-human-feedback.ipynb file instead of creating a dummy node "human_feedback", can I not create a function in this node?
In some nodes or functions, the state field is accessed as State.get('field_name') and some places its State['field_name'], why this approach