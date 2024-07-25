from vector_database import chroma_collection
import streamlit as st 
import os
from typing import TypedDict, Annotated, List
from langgraph.errors import GraphRecursionError
from openai import AzureOpenAI
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.sqlite import SqliteSaver
from flask import Flask, render_template, request, redirect, url_for, session
load_dotenv()
memory = SqliteSaver.from_conn_string(":memory:")
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version="2023-10-01-preview",
    azure_endpoint='https://digitalsolutionnrish.openai.azure.com/',
)
patient_prompt = """You are a helpful medical assistant. For a patient having patient description as {patient_descriptiom} strictly observe patient description especially there age and gender and provided list of medical tests {medical_tests}. Your task is to generate a single useful question asked to the patient so that you can do diagnosis and suggest the patient some medical tests strictly from the medical list.You will be provided more info later.Note the question asked shouldnt be repeated

"""
deciding_prompt = """
You are a helpful medical assistant. For a patient on being asked a question as {question}. The patient answered as {answer} .Output what conclusions you draw from it based on the information given as {info} and also strictly stick to patient description: {patient_description},the patient might not always be senior citizen or female .Stick strictly to the information given
"""
end_prompt = """
You are a helpful medical assistant . You will be given a patient description as {patient_description} . Your task is to check whether the patient description is enough to suggest one particular test strictly focusing on patient's symptoms from the given list as {list} or do you need further information if yes output integer 0 if you need more information . Otherwise output 3 tests by looking at patient description and list along with what you consider gender and age of patient
 
"""
new_node_prompt = """
You are a helpful medical assistant . You will be given a patient description as {patient_description} and a list of packages given by {list}. Your task is to output one test based on the patient description strictly out of the list which should focus precisely on patient's symptoms
"""

def patient_des(age, gender, symptom1, symptom2, smoke_drink):
    description = (
        f"Suggest package for a patient whose profile is given by"
        f"Patient's Profile:\n"
        f"- Age: {age}\n"
        f"- Gender: {gender}\n\n"
        f"Symptoms Reported:\n"
        f"- Primary Symptoms: {symptom1}\n"
        f"- Additional Symptoms: {symptom2}\n\n"
        f"Lifestyle Habits:\n"
        f"- Smoking/Drinking Status: {smoke_drink}\n\n"
        
    )
    return description


def retrival(query:str):
    results = chroma_collection.query(query_texts=[query], n_results=20)
    retrieved_documents = results['documents'][0]
    return retrieved_documents
    


class AgentState(TypedDict):
    patient_des:List[str]
    questions:List[str]
    answers:List[str]
    content:str
    boolean:int
    revision_number:int
    max_revisions:int
    
model="gpt-4-32k"

def patient_des_node(state:AgentState):
    print('Patient_node')
    print('------------------------')
    pd = ''.join(state['patient_des'])
    content = state['content']
    y = state['revision_number']
    print(y)
    messages = [
        {
            'role':'system',
            'content':patient_prompt
            
             
        },
        {
            'role':'user',
            'content':f'patient_description:{pd} .\n medical_tests:{content}'
        }
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages
        
    )
    content = response.choices[0].message.content
    x = state['questions']  or []
    
    x.append(content)
    return {'questions':x , 'revision_number': y+1}

def question_ans(state:AgentState):
    print('Question')
    print('------------------------')
    que = state['questions'][-1]
    ans = state['answers'][-1]
   
    cont = state['content']
    messages = [
        {
            'role':'system',
            'content':deciding_prompt
            
        },
        {
            'role':'user',
            'content':f'question:{que} .\n answer:{ans} .\n info: {cont}'
        }
    
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages
        
    )
    content = response.choices[0].message.content
    x = state['answers'] or []
    x.append(content)
    print(x)
    y = state['patient_des'][0]
    y += content
    print(y)
    
    return {'answers':x,'patient_des':[y]}

def end_node(state:AgentState):
    print('End')
    print('------------------------')
    print(state['patient_des'])
    p = state['patient_des']
    l = state['content']
    messages = [
        {
            'role':'system',
            'content': end_prompt
        },
        {
            'role':'user',
            'content':f'patient_description:{p} .\n list:{l}'
        }
        
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages
        
    )
    content = response.choices[0].message.content
    if content=='0':
       
       return {'boolean':[0,content]}
    else:
        answers = state['answers']
        p = state['patient_des']
        print(content)
        
        return {'boolean':[1,content] }
        
def should_continue(state:AgentState):
    print('-------------------should_continue-------------------')
    if state['boolean'][0]==1:
        return 'end'
    if state['revision_number']>state['max_revisions']:
        return 'new_node'
    return 'patient_description'
def new_node(state:AgentState):

    content = state['content']

    print('New node')
    print('-----------------')
    print(state['patient_des'])
    pd = state['patient_des']
    messages = [
        {
            'role':'system',
            'content':new_node_prompt
        },
        {
            'role':'user',
            'content': f'patient_description:{pd} .\n list:{content}'
        }
    ]
    
    response = client.chat.completions.create(
        model = model,
        messages=messages
    )
    print('Test->',response.choices[0].message.content)
    return {'boolean':[1,response.choices[0].message.content]}

def build_graph(state : AgentState,nodes = [patient_des_node,question_ans,end_node,new_node,should_continue]):
    builder = StateGraph(AgentState)   
    builder.add_node('patient_description',patient_des_node)
    
    builder.add_node('ques_ans',question_ans)
    builder.add_node('end_node',end_node)
    builder.add_node('new_node',new_node)
    builder.set_entry_point('patient_description')
    builder.add_conditional_edges(
        'end_node',
        should_continue,
        {'new_node':'new_node','patient_description':'patient_description','end':END}
        
    )
    builder.add_edge('new_node',END)
    builder.add_edge('patient_description','ques_ans')
  
    builder.add_edge('ques_ans','end_node')
    graph = builder.compile(checkpointer=memory,interrupt_after=['patient_description'])
    print('Graph built')
    return graph

def stream(graph,patient_description,x):
    thread = {"configurable": {"thread_id": "1"}}
    for s in graph.stream({
        'patient_des':[patient_description],
        'content':x,
        'questions':[],
        'answers':[],
        'revision_number':1,
        'max_revisions':6,
        'boolean':0
        
    }, thread):
        print(s)
     

def run(graph,thread,patient_description,list_tests):
    if len(list(graph.get_state(thread).values))==0:
        s =graph.stream({
        'patient_des':[patient_description],
        'content':list_tests,
        'questions':['None'],
        'answers':['None'],
        'revision_number':1,
        'max_revisions':6,
        'boolean':0
        
    }, thread)
        print('11')
        return s
    else:
        print('22')
        s = graph.stream(None,thread)
        return s
                
def recursive_function_1(graph,thread,patient_description,list_tests):
    x = run(graph,thread,patient_description,list_tests)
    for i in x:
        print(i.keys())
        if str(i.keys()) == "dict_keys(['patient_description'])":
            ans = input(i['patient_description']['questions'][-1])
           

        elif(str(i.keys()) == "dict_keys(['end_node'])" and i['end_node']['boolean'][0]==1):
            print('Ans---->',i['end_node']['boolean'][1])
            return i['end_node']['boolean'][1]
        elif(str(i.keys()) == "dict_keys(['new_node'])" and i['new_node']['boolean'][0]==1):
            print('Ans---->',i['new_node']['boolean'][1])
            return i['new_node']['boolean'][1]
            
    current_values = graph.get_state(thread)
    current_values.values['answers'].append(ans)
    graph.get_state(thread).next
    graph.update_state(thread,current_values.values)
    recursive_function_1(graph,thread,patient_description,list_tests)
                

    
    
    
    
