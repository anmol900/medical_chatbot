#from flask import Flask, render_template, request, redirect, url_for, session
from final import *
age = input('age')
gender = input('gender')
sym1 = input('s1')
sym2 = input('s2')
sd = input('sd')

des = patient_des(age,gender,sym1,sym2,sd)
list = retrival(des)

# thread = {"configurable": {"thread_id": "231"}}
# s = AgentState()
# graph = build_graph(s)

# recursive_function_1(graph,thread,des,list)

s = AgentState()
graph = build_graph(s)
thread = {"configurable": {"thread_id": "288"}}

x = graph.stream({
    'patient_des': [des],
    'content': list,
    'questions': ['None'],
    'answers': ['None'],
    'revision_number':1,
    'max_revisions':6,
    'boolean':0
}, thread)


def rec_check(x):
    
    for i in x:
        if str(i.keys()) == "dict_keys(['end_node'])" and i['end_node']['boolean'][0] == 1:
            return i['end_node']['boolean'][1]
        elif str(i.keys()) == "dict_keys(['new_node'])" and i['new_node']['boolean'][0] == 1:
            return i['new_node']['boolean'][1]
        for j in i.values():
            print(j)
    print(str(graph.get_state(thread).next))
    current_values = graph.get_state(thread)
    ans = input(current_values.values['questions'][-1])
    current_values.values['answers'].append(ans)
    graph.update_state(thread,current_values.values)
    y = run(graph,thread,des,list)
    return rec_check(y)

print(rec_check(x))    
        
   
    
    
    
    
    
    
    
    
    
    

