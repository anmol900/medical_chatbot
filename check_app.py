from flask import Flask, render_template, request, redirect, url_for, session
import os
from dotenv import load_dotenv
from final import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for session management

# Initialize the graph
s = AgentState()
graph = build_graph(s)

# Function to retrieve patient description
def patient_des(age, gender, symptom1, symptom2, smoke_drink):
    description = (
        f"Suggest package for a patient whose profile is given by:\n\n"
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

# def get_user_input(question):
#     question = session.get('question', 'No question available')
#     # if request.method == 'POST':
#     #     user_input = request.form['user_input']
#     #     # return redirect(url_for('process_input', user_input=user_input))
#     #     return user_input
#     return render_template('input_form.html', question=question)


# def get_user_input(question):
#     """
#     Displays a form with the given question and returns the user's input.
#     """
#     print(request.method)
#     if request.method == 'POST':
#         return request.form['user_input']
#     else:
#         return render_template('input_form.html', question=question)

def get_user_input(question):
    print(request.method)
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if user_input:
            return user_input
        else:
            return "Input was not provided."
    else:
        return render_template('input_form.html', question=question)


# Function to handle the recursive chatbot interaction
# def rec(graph, thread, patient_description, list_tests):
#     x = run(graph, thread, patient_description, list_tests)
#     for i in x:
#         print(f"Keys: {i.keys()}")
#         print(graph.get_state(thread).values['answers'])
#         print('*************************************')
#         print(graph.get_state(thread).values['questions'])
#         print('+++++++++++++++++++++++++++++++++++++++++')
#         print(graph.get_state(thread).values['patient_des'])
        
            
#         if str(i.keys()) == "dict_keys(['end_node'])" and i['end_node']['boolean'][0] == 1:
#             return render_template('result.html', result=i['end_node']['boolean'][1])
#         elif str(i.keys()) == "dict_keys(['new_node'])" and i['new_node']['boolean'][0] == 1:
#             return render_template('result.html', result=i['new_node']['boolean'][1])
#     print(graph.get_state(thread).next)
#     current_values = graph.get_state(thread)
#     ques = current_values.values['questions'][-1]
#     print(ques)
    
#     if len(ques) > 0:
#         result = get_user_input(ques)
#         if isinstance(result,str):
#             ans = result
#             print('-------------++++')
#             print(ans)
#             #can u add a function like ans = input(current_values.values['questions'][-1]) but in flask
#             current_values.values['answers'].append(ans)
#             graph.get_state(thread).next
#             graph.update_state(thread,current_values.values)
#         else:
#             return result
    
    
#     return rec(graph, thread, patient_description, list_tests)
             
def rec(graph, thread, patient_description, list_tests):
    x = run(graph, thread, patient_description, list_tests)
    for i in x:
        # print(f"Keys: {i.keys()}")
        # print(graph.get_state(thread).values['answers'])
        # print('*************************************')
        # print(graph.get_state(thread).values['questions'])
        # print('+++++++++++++++++++++++++++++++++++++++++')
        # print(graph.get_state(thread).values['patient_des'])
        
        if 'end_node' in i and i['end_node']['boolean'][0] == 1:
            return render_template('result.html', result=i['end_node']['boolean'][1])
        elif 'new_node' in i and i['new_node']['boolean'][0] == 1:
            return render_template('result.html', result=i['new_node']['boolean'][1])
    
    # print(graph.get_state(thread).next)
    current_values = graph.get_state(thread)
    ques = current_values.values['questions'][-1]
    print(ques)
    
    # if request.method == "POST":
    print(request.method)
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if user_input:
            if isinstance(user_input, str):
                ans = user_input
                print("Answer:", ans)
                print('-------------++++')
                current_values.values['answers'].append(ans)
                graph.get_state(thread).next
                graph.update_state(thread, current_values.values)
                # return "rec(graph, thread, patient_description, list_tests)"
                return render_template('input_form.html', question=ques)
            else:
                return user_input
       
    else:
        return render_template('input_form.html', question=ques)
    
    # render_template('input_form.html', question=ques)
    
   

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        age = request.form['age']
        gender = request.form['gender']
        sm1 = request.form['symptom1']
        sm2 = request.form['symptom2']
        sd = request.form['smoke_drink']
        des = patient_des(age, gender, sm1, sm2, sd)
        session['description'] = des
        list_test = retrival(des)
        session['list_tests'] = list_test
        session['thread'] = {'configurable': {'thread_id': '120'}}
        return redirect(url_for('desc'))
    return render_template('index.html')

@app.route('/desc',methods=['GET','POST'])
def desc():
    # print(request.form['text'])
    des = session.get('description', 'No description available')
    lt = session.get('list_tests', 'null')
    thread = session.get('thread', 'null')
 
    return rec(graph=graph, thread=thread, patient_description=des, list_tests=lt)

if __name__ == '__main__':
    app.run(debug=True)
