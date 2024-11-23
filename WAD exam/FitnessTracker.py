import socket
import mimetypes
import psycopg2
import json
from datetime import date


conn = psycopg2.connect(
    dbname="fitnesstracker",
    user="postgres",
    password="Sunil@18",
    host="Localhost"
    )
cur = conn.cursor()

def run_server(host='127.0.0.1',port=6969):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server is running on {host}:{port}")
        print("Press Ctrl+C to stop the server.")
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connected by {addr}")

            request = client_socket.recv(2048).decode('utf-8')
            print(f"Request received:\n{request}")

            response = handleRequest(request)
            client_socket.sendall(response)
            client_socket.close()
 
def serverFile(file_path):
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except:
        return f"HTTP/1.1 404 NOT FOUND\n\n file not found".encode()

def userInput(request):
    body = request.split('\r\n\r\n')[1]
    postData = body
    formData = {}
    for pair in postData.split('&'):
        key, value = pair.split('=')
        formData[key] = value
    return formData

sessions = {}
def handleRequest(request):
    global conn

    parseRequest = request.split('\n')[0].split()
    method = parseRequest[0]
    uri = parseRequest[1]

    cookie = request.split('\n')
    for line in cookie:
        if 'Cookie:' in line:
            a = line.split(':')[1].strip()
            session = a.split('=')[1]

    if uri == '/favicon.ico':
        return ''.encode()
    
    if method == 'GET':
        if uri  == '/' or uri == '/home':
            if True in sessions.values():
                response = f'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'.encode() + serverFile('home.html')
            else:
                response = f'HTTP/1.1 302 FOUND\r\nLocation: /login\r\n\r\n'.encode()

        if uri == '/login':
            if True in sessions.values():
                response =f'HTTP/1.1 302 FOUND\r\nLocation: /home\r\n\r\n'.encode()
            else:
                response = f'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'.encode() + serverFile('login.html')
        
        elif uri == '/register':
            if True in sessions.values():
                response =f'HTTP/1.1 302 FOUND\r\nLocation: /home\r\n\r\n'.encode()
            else:
                response = f'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'.encode() + serverFile('register.html')

        elif uri == '/logs?':
            response = f'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'.encode() + serverFile('activity.html')

        elif uri == '/api/logs':
            cur = conn.cursor()
            cur.execute(f"""SELECT username, activity_date, steps, calories, hours_slept
                                FROM user_activity
                                WHERE 
                                    username = '{session}'
                                    AND TO_DATE(activity_date, 'YYYY-MM-DD') >= DATE_TRUNC('week', CURRENT_DATE)
                                    AND TO_DATE(activity_date, 'YYYY-MM-DD') < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days';
                                """)
            logs = cur.fetchall()
            conn.commit()            
            
            response = ('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + json.dumps(logs)).encode()

        elif uri == '/api/goal':
            cur = conn.cursor()
            cur.execute(f"""SELECT username, activity_date, steps, calories, hours_slept
                                FROM user_goal
                                WHERE username = '{session}'
                                AND TO_DATE(activity_date, 'YYYY-MM-DD') >= DATE_TRUNC('week', CURRENT_DATE)
                                AND TO_DATE(activity_date, 'YYYY-MM-DD') < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days';

                                """)
            goals = cur.fetchall()
            conn.commit()            
            
            response = ('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + json.dumps(goals)).encode()

        elif uri.endswith('.css'): #/scrit.js
            response = (f'HTTP/1.1 200 OK\nContent-Type: text/css\n\n').encode() + serverFile(uri[1:].strip())
        
        elif uri.endswith('.js'): #/scrit.js
            response = (f'HTTP/1.1 200 OK\nContent-Type: text/css\n\n').encode() + serverFile(uri[1:].strip())
        
        elif uri == '/logout':
            if True in sessions.values():
                for key, value in sessions.items():
                    sessions[key] = False
                response = f"HTTP/1.1 302 FOUND\nLocation: /login\nSet-Cookie: session_id=; Max-Age=0\r\n\r\n".encode()
            else:
                response = f"HTTP/1.1 302 FOUND\nLocation: /login\nSet-Cookie: session_id=; Max-Age=0\r\n\r\n".encode()
        return response
    
    elif method == 'POST':
        if uri == '/register':
            formData = userInput(request)
            print(formData)
            username = formData.get('username')
            email = formData.get('email').replace('%40', '@')
            password = formData.get('password')
            
            cur = conn.cursor()
            cur.execute(f"INSERT into users values('{username}', '{email}', '{password}');")
            conn.commit()            
            cur.close()

            response = f'HTTP/1.1 302 FOUND\r\nLocation: /login\r\n\r\n'.encode()

        elif uri == '/login':
            formData = userInput(request)
            # print(formData)
            username = formData.get('username')
            password = formData.get('password')

            cur = conn.cursor()
            cur.execute(f"SELECT EXISTS (SELECT 1 FROM users WHERE username = '{username}' AND password = '{password}') AS password_exists;")
            password_exists = cur.fetchone()[0]
            # print(password_exists)
            cur.close()

            if password_exists:
                session_id = username
                sessions[session_id] = True
                # print('sessions:\n',sessions)
                response = f'HTTP/1.1 302 FOUND\nLocation: /home\nSet-Cookie: session_id={session_id}\n\n'.encode()
            else:
                response = (f'HTTP/1.1 200 OK\nContent-Type: {mimetypes}\n\n').encode() + serverFile('login.html') + '<script>document.getElementById("invalid").innerHTML = "<p>Invalid username or password</p>";</script>'.encode()

        elif uri == '/add-activity':
            formData = userInput(request)
            steps = formData.get('steps')
            calories = formData.get('calories')
            sleep = formData.get('sleep')
            activityDate = formData.get('activityDate')

            cur = conn.cursor()
            cur.execute(f"INSERT into user_activity values('{session}','{activityDate}', '{steps}', '{calories}', {sleep});")
            conn.commit()            
            cur.close()
            
            response =f'HTTP/1.1 302 FOUND\r\nLocation: /home\r\n\r\n'.encode()
        
        elif uri == '/set-goal':
            formData = userInput(request)
            steps = formData.get('steps')
            calories = formData.get('calories')
            sleep = formData.get('sleep')
            current_date = date.today()

            print(current_date)


            cur = conn.cursor()
            try:
                cur.execute(f"""
                INSERT INTO user_goal (username, activity_date, steps, calories, hours_slept)
                SELECT '{session}', '{current_date}', {steps}, {calories}, {sleep}
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM user_goal
                    WHERE username = '{session}' 
                    AND TO_DATE(activity_date, 'YYYY-MM-DD') >= DATE_TRUNC('week', CURRENT_DATE)
                    AND TO_DATE(activity_date, 'YYYY-MM-DD') < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days'
                );
                """)
                response =f'HTTP/1.1 302 FOUND\r\nLocation: /home\r\n\r\n'.encode()
            except:
                # response =f'HTTP/1.1 302 FOUND\r\nLocation: /home\r\n\r\n'.encode() 
                response =f'HTTP/1.1 200 OK\r\nContent-Type:text/html\r\n\r\n'.encode() + serverFile('home.html') + '<script>document.getElementById("error").innerHTML = "<h3>Goal Already set!</h3>";'.encode()

            conn.commit()            
            cur.close()
            



        return response
    

if __name__ == '__main__':
     run_server()
